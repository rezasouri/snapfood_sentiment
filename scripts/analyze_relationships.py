"""Measure exact key joins and ambiguity without copying customer text."""
from __future__ import annotations

import csv
import json

import duckdb

from common import ROOT, configure, relation, save_json, load_inventory


def join_coverage(total: int, matched: int) -> float:
    return matched / total if total else 0.0


def main() -> None:
    configure()
    inv = load_inventory()
    c = duckdb.connect()
    for n, item in inv.items():
        if item["access"] != "records_accessible":
            raise RuntimeError(f"{n} inaccessible: {item.get('blocker')}")
        relation(c, item["local_files"], n.replace("-", "_"))
    c.sql("CREATE TEMP VIEW menu_alias_map AS SELECT alias, count(*) menu_rows, count(DISTINCT vendor_code) vendor_count, min(vendor_code) sole_vendor FROM snappfood_menus GROUP BY alias")
    specs = [
        ("replies_to_reviews", "snappfood_review_replies p", "snappfood_reviews r", "p.review_id=r.id", "p.review_id", "r.id"),
        ("menus_to_vendors", "snappfood_menus m", "snappfood_vendors v", "m.vendor_code=v.vendorCode", "m.vendor_code", "v.vendorCode"),
        ("reviews_to_menu_alias", "snappfood_reviews r", "menu_alias_map m", "r.product_alias=m.alias", "r.product_alias", "m.alias"),
        ("reviews_to_vendor_code_direct", "snappfood_reviews r", "snappfood_vendors v", "r.product_alias=v.vendorCode", "r.product_alias", "v.vendorCode"),
    ]
    rows=[]
    for label,left,right,on,lkey,rkey in specs:
        total=c.sql(f"SELECT count(*) FROM {left}").fetchone()[0]
        matched=c.sql(f"SELECT count(*) FROM {left} SEMI JOIN {right} ON {on}").fetchone()[0]
        distinct_right=c.sql(f"SELECT count(DISTINCT {rkey}) FROM {right}").fetchone()[0]
        right_total=c.sql(f"SELECT count(*) FROM {right}").fetchone()[0]
        rows.append({"relation":label,"left_rows":total,"matched_left_rows":matched,"unmatched_left_rows":total-matched,"coverage":join_coverage(total,matched),"right_rows":right_total,"distinct_right_keys":distinct_right,"basis":"full_dataset_exact_identifier_join"})
    ambiguous=c.sql("SELECT count(*) FROM snappfood_reviews r JOIN menu_alias_map m ON r.product_alias=m.alias WHERE m.vendor_count>1").fetchone()[0]
    menu_dup=c.sql("SELECT count(*) FILTER (WHERE menu_rows>1), count(*) FILTER (WHERE vendor_count>1), max(menu_rows) FROM menu_alias_map").fetchone()
    review_vendor_unambiguous=c.sql("SELECT count(*) FROM snappfood_reviews r JOIN menu_alias_map m ON r.product_alias=m.alias WHERE m.vendor_count=1").fetchone()[0]
    c.sql("CREATE TEMP VIEW item_mapping_status AS SELECT CASE WHEN mi.id IS NOT NULL AND mi.alias=r.product_alias THEN 'exact_item' WHEN mi.id IS NOT NULL THEN 'id_collision' WHEN a.vendor_count=1 THEN 'alias_unique_vendor_only' ELSE 'alias_ambiguous_only' END status FROM snappfood_reviews r LEFT JOIN snappfood_menus mi ON r.product_alias=CAST(mi.id AS VARCHAR) JOIN menu_alias_map a ON r.product_alias=a.alias")
    statuses=dict(c.sql("SELECT status,count(*) FROM item_mapping_status GROUP BY 1").fetchall())
    item_stats=c.sql("SELECT count(*) items, median(n) median_reviews, count(*) FILTER (WHERE n>=30) items_ge_30, count(*) FILTER (WHERE n>=100) items_ge_100 FROM (SELECT m.id,count(*) n FROM snappfood_reviews r JOIN snappfood_menus m ON r.product_alias=CAST(m.id AS VARCHAR) AND r.product_alias=m.alias GROUP BY 1)").fetchone()
    total=rows[2]["left_rows"]
    details={"reviews_ambiguous_vendor_rows_by_alias_only":ambiguous,"reviews_unique_vendor_rows_by_alias_only":review_vendor_unambiguous,"reviews_unique_vendor_coverage_by_alias_only":join_coverage(total,review_vendor_unambiguous),"item_mapping_status":statuses,"conservative_vendor_rows":statuses["exact_item"]+statuses["alias_unique_vendor_only"],"conservative_vendor_coverage":join_coverage(total,statuses["exact_item"]+statuses["alias_unique_vendor_only"]),"exact_item_coverage":join_coverage(total,statuses["exact_item"]),"exact_items_with_reviews":item_stats[0],"median_reviews_per_matched_item":item_stats[1],"matched_items_ge_30_reviews":item_stats[2],"matched_items_ge_100_reviews":item_stats[3],"menu_aliases_repeated":menu_dup[0],"menu_aliases_multiple_vendors":menu_dup[1],"max_menu_rows_per_alias":menu_dup[2],"review_menu_raw_join_rows":c.sql("SELECT count(*) FROM snappfood_reviews r JOIN snappfood_menus m ON r.product_alias=m.alias").fetchone()[0],"note":"Exact item requires product_alias=CAST(menu.id AS VARCHAR)=menu.alias on the same unique menu row. Numeric id-only collisions are excluded. Alias-only vendor mapping requires exactly one vendor_code."}
    save_json(ROOT/"reports"/"join_details.json",details)
    with (ROOT/"reports"/"join_analysis.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)


if __name__ == "__main__": main()
