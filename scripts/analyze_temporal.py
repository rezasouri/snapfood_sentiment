"""Validate Persian Jalali review dates separately from collection timestamps."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

import duckdb
import jdatetime

from common import ROOT, configure, relation, save_json, load_inventory

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def parse_review_date(value: str | None):
    if not value: return None
    try:
        parts = value.translate(PERSIAN_DIGITS).split("/")
        if len(parts) != 3: return None
        year, month, day = map(int, parts)
        if not 1300 <= year <= 1500: return None
        return jdatetime.date(year, month, day).togregorian()
    except (ValueError, TypeError):
        return None


def main() -> None:
    configure(); inv=load_inventory(); c=duckdb.connect();out={}
    for name in ("snappfood-reviews","snappfood-review-replies"):
        item=inv[name]
        if item["access"]!="records_accessible": out[name]={"status":"blocked"};continue
        view=name.replace("-","_");relation(c,item["local_files"],view)
        dates=c.sql(f"SELECT date,count(*) FROM {view} GROUP BY 1").fetchall()
        parsed=[(parse_review_date(d),n) for d,n in dates]
        valid=[(d,n) for d,n in parsed if d is not None]
        total=sum(n for _,n in dates);valid_count=sum(n for _,n in valid)
        monthly=Counter();weekly=Counter()
        for d,n in valid:
            monthly[d.strftime("%Y-%m")]+=n;weekly[d.strftime("%G-W%V")]+=n
        result={"rows":total,"valid_review_date_rows":valid_count,"invalid_or_missing_review_date_rows":total-valid_count,"date_range_gregorian":[str(min(d for d,_ in valid)),str(max(d for d,_ in valid))] if valid else None,"months":dict(sorted(monthly.items())),"weeks":dict(sorted(weekly.items())),"date_basis":"date field parsed as Jalali; fetched_at is collection time"}
        if "fetched_at" in item["parquet_schema"]:
            result["fetched_at_range"]=c.sql(f"SELECT min(fetched_at),max(fetched_at) FROM {view}").fetchone()
        out[name]=result
    if all(inv[n]["access"] == "records_accessible" for n in ("snappfood-reviews", "snappfood-menus")):
        relation(c,inv["snappfood-menus"]["local_files"],"menus")
        c.sql("CREATE TEMP VIEW alias_map AS SELECT alias,count(DISTINCT vendor_code) vendors,min(vendor_code) vendor FROM menus GROUP BY alias")
        c.sql("CREATE TEMP VIEW mapped AS SELECT r.date, CASE WHEN mi.id IS NOT NULL AND mi.alias=r.product_alias THEN mi.vendor_code WHEN mi.id IS NULL AND a.vendors=1 THEN a.vendor ELSE NULL END vendor FROM snappfood_reviews r LEFT JOIN menus mi ON r.product_alias=CAST(mi.id AS VARCHAR) JOIN alias_map a ON r.product_alias=a.alias")
        cells=c.sql("SELECT count(*),count(*) FILTER (WHERE n>=30),count(*) FILTER (WHERE n>=100),sum(n) FILTER (WHERE n>=30) FROM (SELECT vendor,substr(date,1,7) ym,count(*) n FROM mapped WHERE vendor IS NOT NULL GROUP BY 1,2)").fetchone()
        vendor_stats=c.sql("SELECT count(*),median(n),count(*) FILTER (WHERE n>=100) FROM (SELECT vendor,count(*) n FROM mapped WHERE vendor IS NOT NULL GROUP BY 1)").fetchone()
        out["conservative_vendor_month"]={"observed_cells":cells[0],"cells_ge_30":cells[1],"cells_ge_100":cells[2],"reviews_in_cells_ge_30":cells[3],"vendors":vendor_stats[0],"median_reviews_per_vendor":vendor_stats[1],"vendors_ge_100_reviews":vendor_stats[2]}
    save_json(ROOT/"reports"/"temporal_analysis.json",out)


if __name__ == "__main__":main()
