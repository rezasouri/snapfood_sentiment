"""Transparent keyword exploration; counts are candidates, never gold labels."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter

import duckdb

from common import ROOT, configure, relation, sample_sql, save_json, load_inventory

PATTERNS = {
    "taste_quality": r"طعم|مزه|خوشمزه|بی.?کیفیت|کیفیت|بدمزه",
    "temperature": r"سرد|داغ|گرم|یخ کرده",
    "packaging": r"بسته.?بندی|ظرف|نایلون|پلاستیک|نشتی",
    "price_value": r"قیمت|گرون|گران|ارزون|ارزان|تخفیف",
    "delivery_delay": r"دیر|تاخیر|تأخیر|زمان ارسال|تحویل",
    "courier": r"پیک|موتوری|راننده",
    "portion": r"حجم|کم بود|اندازه|پرس|مقدار",
    "missing_wrong": r"اشتباه|کمبود|جا افتاد|نفرستاد|نیاورد|سفارش.*نبود",
    "service": r"برخورد|پاسخگو|پشتیبانی|رفتار",
}


def candidate_aspects(text: str) -> list[str]:
    return [k for k,p in PATTERNS.items() if re.search(p,text or "")]


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument("--sample-size",type=int,default=20000);p.add_argument("--seed",type=int,default=42);args=p.parse_args()
    configure(); inv=load_inventory(); item=inv["snappfood-reviews"]
    if item["access"]!="records_accessible": raise RuntimeError(item.get("blocker"))
    c=duckdb.connect();relation(c,item["local_files"],"reviews")
    records=c.sql(f"SELECT id,comment_text,feeling,rate FROM ({sample_sql('reviews',args.sample_size,args.seed)})").fetchall()
    counts=Counter(); aspect_n=Counter(); examples=[]
    for rid,text,feeling,rate in records:
        aspects=candidate_aspects(text or "")
        counts.update(aspects);aspect_n[len(aspects)]+=1
        if len(examples)<30 and (len(aspects)>=2 or (text and len(text.split())<4)):
            examples.append({"review_id":rid,"aspects":aspects,"feeling":feeling,"rate":rate})
    save_json(ROOT/"reports"/"text_analysis.json",{"sample_size":len(records),"seed":args.seed,"method":"stable id hash sample","aspect_keyword_candidates":dict(counts),"candidate_aspects_per_review":dict(aspect_n),"manual_inspection_candidates":examples,"caveat":"Keyword hits are not ABSA labels; review IDs allow authorized local inspection without publishing customer text."})


if __name__ == "__main__": main()
