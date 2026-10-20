"""Deterministic rating/year sampling with vendor coverage within each stratum."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import duckdb
from huggingface_hub import hf_hub_download


def allocate_strata(counts: dict[tuple[int, int], int], size: int) -> dict[tuple[int, int], int]:
    """Reserve one per stratum then allocate remaining capacity proportionally."""
    if size <= 0 or size > sum(counts.values()) or any(n <= 0 for n in counts.values()):
        raise ValueError("sample size must fit a nonempty eligible population")
    keys = sorted(counts, key=lambda key: (-counts[key], key))
    quotas = {key: int(index < size) for index, key in enumerate(keys)}
    remaining = size - sum(quotas.values())
    capacities = {key: counts[key] - quotas[key] for key in keys}
    total_capacity = sum(capacities.values())
    if remaining:
        exact = {key: remaining * capacities[key] / total_capacity for key in keys}
        for key in keys:
            quotas[key] += int(exact[key])
        leftover = size - sum(quotas.values())
        order = sorted(keys, key=lambda key: (-(exact[key] - int(exact[key])), key))
        for key in order[:leftover]:
            quotas[key] += 1
    return quotas


def attach_source_views(connection: duckdb.DuckDBPyConnection, lock: dict) -> None:
    for dataset, name in [("snappfood-reviews", "reviews"), ("snappfood-menus", "menus"), ("snappfood-vendors", "vendors")]:
        item = lock["datasets"][dataset]
        files = [hf_hub_download(repo_id=item["repo"], repo_type="dataset", revision=item["revision"], filename=f["name"]) for f in item["files"]]
        connection.from_parquet(files).create_view(name, replace=True)


def create_eligible_view(connection: duckdb.DuckDBPyConnection) -> None:
    """Mirror the audited rule: same-row ID+alias, or no ID match and one vendor."""
    connection.sql("CREATE TEMP VIEW alias_map AS SELECT alias,count(DISTINCT vendor_code) vendor_count,min(vendor_code) sole_vendor FROM menus GROUP BY alias")
    connection.sql("""
        CREATE TEMP VIEW mapped AS
        SELECT r.*, CASE
          WHEN m.id IS NOT NULL AND m.alias=r.product_alias THEN m.vendor_code
          WHEN m.id IS NULL AND a.vendor_count=1 THEN a.sole_vendor
          ELSE NULL END AS vendor_code,
          CASE WHEN m.id IS NOT NULL AND m.alias=r.product_alias
            THEN 'exact_item' ELSE 'unique_alias_vendor' END AS mapping_basis
        FROM reviews r LEFT JOIN menus m ON r.product_alias=CAST(m.id AS VARCHAR)
        LEFT JOIN alias_map a ON r.product_alias=a.alias
    """)
    connection.sql("""
        CREATE TEMP VIEW eligible AS
        SELECT CAST(r.id AS VARCHAR) review_id, r.comment_text AS "text", r.vendor_code,
          r.mapping_basis, r.date review_date, CAST(r.rating AS INTEGER) rating,
          CAST(translate(substr(r.date,1,4),'۰۱۲۳۴۵۶۷۸۹','0123456789') AS INTEGER) AS "year"
        FROM mapped r SEMI JOIN vendors v ON r.vendor_code=v.vendorCode
        WHERE trim(r.comment_text)<>'' AND r.rating IN (0,2,4,6,8,10)
          AND regexp_full_match(translate(r.date,'۰۱۲۳۴۵۶۷۸۹','0123456789'), '[0-9]{4}/[0-9]{2}/[0-9]{2}')
    """)


def select_sample(connection: duckdb.DuckDBPyConnection, quotas: dict, seed: int) -> list[dict]:
    connection.execute("CREATE TEMP TABLE quotas(year INTEGER,rating INTEGER,quota INTEGER)")
    connection.executemany("INSERT INTO quotas VALUES (?,?,?)", [(year,rating,n) for (year,rating),n in sorted(quotas.items())])
    # SHA-256 is stable across engine versions. Round-robin by vendor avoids a few
    # high-volume vendors taking every slot within a year/rating stratum.
    rows = connection.execute("""
        WITH vendor_order AS (
          SELECT *,row_number() OVER (PARTITION BY year,rating,vendor_code
            ORDER BY sha256(review_id || '|' || CAST(? AS VARCHAR)),review_id) vendor_rank
          FROM eligible
        ), stratum_order AS (
          SELECT *,row_number() OVER (PARTITION BY year,rating
            ORDER BY vendor_rank,sha256(vendor_code || '|' || CAST(? AS VARCHAR)),review_id) stratum_rank
          FROM vendor_order
        ) SELECT s.review_id,s.text,s.vendor_code,s.mapping_basis,s.review_date,s.rating,s.year
          FROM stratum_order s JOIN quotas q USING(year,rating)
          WHERE s.stratum_rank<=q.quota ORDER BY s.year,s.rating,s.stratum_rank
    """, [seed,seed]).fetchall()
    names = [d[0] for d in connection.description]
    return [dict(zip(names,row)) for row in rows]


def prepare_sample(lock_path: Path, output: Path, report_path: Path, size: int, seed: int) -> dict:
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    lock = json.loads(lock_path.read_text())
    output.parent.mkdir(parents=True,exist_ok=True)
    con = duckdb.connect(config={"memory_limit":"2GB","threads":4,"temp_directory":str(output.parent/"tmp")})
    attach_source_views(con, lock)
    create_eligible_view(con)
    counts = {(year,rating): n for year,rating,n in con.sql("SELECT year,rating,count(*) FROM eligible GROUP BY 1,2").fetchall()}
    quotas = allocate_strata(counts,size)
    records = select_sample(con,quotas,seed)
    if len(records) != size or len({r["review_id"] for r in records}) != size:
        raise ValueError("sample size/ID integrity check failed")
    content = "".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in records)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(content,encoding="utf-8")
    report = {
        "sample_size": len(records), "seed": seed, "eligible_population":sum(counts.values()),
        "sample_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "dataset_revisions":{n:i["revision"] for n,i in lock["datasets"].items()},
        "method":"minimum-one + largest-remainder rating/year quotas; vendor round-robin ordered by SHA-256",
        "strata":[{"year":year,"rating":rating,"population":counts[year,rating],"sample":quotas[year,rating]} for year,rating in sorted(counts)],
        "sample_vendors":len({r["vendor_code"] for r in records}),
        "mapping_counts":dict(Counter(r["mapping_basis"] for r in records)),
        "duplicate_text_rows":len(records)-len({r["text"] for r in records}),
        "limitations":["Vendor balancing and minimum quotas are not population-proportional; do not use pilot counts as population issue rates.","Rating zero is retained as a separate undocumented/unrated stratum; rating 20 is excluded.","Review year is Jalali, not collection year. Historical mapping validity is still unverified."],
    }
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    con.close()
    return report


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lock",type=Path,default=Path("configs/snappfood.lock.json"))
    p.add_argument("--output",type=Path,default=Path("data/pilot/reviews.jsonl"))
    p.add_argument("--report",type=Path,default=Path("reports/pilot_sample.json"))
    p.add_argument("--size",type=int,default=1000)
    p.add_argument("--seed",type=int,default=42)
    args=p.parse_args()
    report=prepare_sample(args.lock,args.output,args.report,args.size,args.seed)
    print(json.dumps({"event":"sample_prepared","rows":report["sample_size"],"vendors":report["sample_vendors"]}))


if __name__ == "__main__": main()
