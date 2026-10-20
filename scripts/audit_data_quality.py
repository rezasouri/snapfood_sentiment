"""Full-count field/ID audit and bounded deterministic review-text sample."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from importlib.metadata import version
from collections import Counter

import duckdb

from common import ROOT, configure, relation, sample_sql, save_json, load_inventory

PERSIAN = re.compile(r"[\u0600-\u06ff]")
LATIN = re.compile(r"[A-Za-z]")
URL = re.compile(r"https?://|www\.", re.I)
HTML = re.compile(r"<[^>]+>")
EMOJI = re.compile(r"[\U0001f300-\U0001faff]")


def text_features(s: str) -> dict[str, int]:
    return {"persian": bool(PERSIAN.search(s)), "latin": bool(LATIN.search(s)), "arabic_yeh": "ي" in s, "arabic_kaf": "ك" in s, "zwnj": "\u200c" in s, "emoji": bool(EMOJI.search(s)), "url": bool(URL.search(s)), "html": bool(HTML.search(s)), "chars": len(s), "words": len(s.split())}


def duplicate_count(values: list[object]) -> int:
    return len(values) - len(set(values))


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("ي", "ی").replace("ك", "ک")
    value = re.sub(r"[\W_]+", "", value, flags=re.UNICODE)
    return re.sub(r"(.)\1{2,}", r"\1\1", value)


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--sample-size", type=int, default=20000); p.add_argument("--seed", type=int, default=42); args = p.parse_args()
    configure()
    inventory = load_inventory()
    con = duckdb.connect()
    out = {"settings": vars(args), "dependencies": {name: version(name) for name in ("duckdb", "pyarrow", "huggingface-hub", "jdatetime")}, "dataset_revisions": {name: item["revision"] for name,item in inventory.items()}, "datasets": {}}
    for name, item in inventory.items():
        if item["access"] != "records_accessible":
            out["datasets"][name] = {"status": "blocked", "reason": item.get("blocker")}; continue
        view = name.replace("-", "_")
        relation(con, item["local_files"], view)
        cols = list(item["parquet_schema"])
        n = con.sql(f"SELECT count(*) FROM {view}").fetchone()[0]
        fields = {}
        for col in cols:
            q = f'SELECT count(*) FILTER (WHERE "{col}" IS NULL), count(*) FILTER (WHERE trim(CAST("{col}" AS VARCHAR)) = \'\') FROM {view}'
            nulls, empties = con.sql(q).fetchone()
            fields[col] = {"null": nulls, "empty": empties, "denominator": n, "scope": "full"}
        id_stats = con.sql(f"SELECT count(*)-count(DISTINCT id), count(DISTINCT id) FROM {view}").fetchone()
        result = {"status": "audited", "rows": n, "scope": "full unless labeled sample", "fields": fields, "duplicate_id_rows": id_stats[0], "distinct_ids": id_stats[1]}
        if "comment_text" in cols:
            result["duplicate_text_rows"] = con.sql(f"SELECT count(*)-count(DISTINCT comment_text) FROM {view} WHERE comment_text IS NOT NULL").fetchone()[0]
            result["sample"] = {"size": min(n,args.sample_size), "seed": args.seed, "method": "lowest stable hash(id, seed); duplicate IDs retain stable id order"}
            extra = ", feeling, rating" if "feeling" in cols and "rating" in cols else ""
            sample = con.sql(f"SELECT comment_text, id{extra} FROM ({sample_sql(view,args.sample_size,args.seed)})").fetchall()
            feats = [text_features(row[0] or "") for row in sample]
            result["sample"]["text"] = {k: {"count": sum(int(x[k]) for x in feats), "denominator": len(feats)} for k in feats[0] if k not in ("chars","words")} if feats else {}
            for k in ("chars","words"):
                a=sorted(x[k] for x in feats)
                result["sample"][k+"_quantiles"] = {str(q):a[int((len(a)-1)*q)] for q in (0,.1,.5,.9,.99,1)} if a else {}
            result["sample"]["short_under_4_words"] = sum(x["words"]<4 for x in feats)
            result["sample"]["normalized_duplicate_rows_proxy"] = duplicate_count([normalized_text(row[0] or "") for row in sample])
            result["sample"]["normalized_duplicate_note"] = "Normalization proxy only; does not measure semantic near duplicates"
            if extra:
                complaint = re.compile(r"سرد|دیر|تاخیر|تأخیر|سوخته|بی.?کیفیت|اشتباه|خراب|نفرستاد")
                praise = re.compile(r"عالی|خوشمزه|خوب بود|راضی")
                result["sample"]["happy_with_complaint_term"] = sum(feeling == "HAPPY" and bool(complaint.search(s or "")) for s,_,feeling,_ in sample)
                result["sample"]["sad_with_praise_term"] = sum(feeling == "SAD" and bool(praise.search(s or "")) for s,_,feeling,_ in sample)
                result["sample"]["rating_text_conflict_note"] = "Keyword candidates only; mixed-aspect reviews are not necessarily mislabeled"
        for col in ("feeling","rate","rating","source","city"):
            if col in cols:
                result[col+"_distribution"] = con.sql(f'SELECT CAST("{col}" AS VARCHAR), count(*) FROM {view} GROUP BY 1 ORDER BY 2 DESC LIMIT 30').fetchall()
        if "rate" in cols and "rating" in cols:
            result["rate_rating_disagreement_rows"] = con.sql(f"SELECT count(*) FROM {view} WHERE rate IS DISTINCT FROM rating").fetchone()[0]
        if "feeling" in cols and "rating" in cols:
            result["feeling_rating_cross"] = con.sql(f"SELECT feeling,rating,count(*) FROM {view} GROUP BY 1,2 ORDER BY 1,2").fetchall()
        out["datasets"][name] = result
    save_json(ROOT / "reports" / "metrics.json", out)


if __name__ == "__main__": main()
