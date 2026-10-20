"""Prepare pinned public gold benchmarks without redistributing review text."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import unicodedata
import urllib.request
from importlib.metadata import version
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .contracts import ReviewExtraction

LOG = logging.getLogger(__name__)
PARSINLU_ASPECTS = {
    "طعم": "taste_quality", "کیفیت": "taste_quality",
    "بسته بندی": "packaging", "ارزش خرید": "price_value",
}
# Exact curated terms only. A phone's build/display quality is not food quality.
PARS_ABSA_ASPECTS = {
    "قیمت": "price_value", "قیمتش": "price_value", "ارزش خرید": "price_value",
    "قیمت محصول": "price_value", "ارزش خریدش": "price_value",
    "قیمت این محصول": "price_value", "بسته بندی": "packaging",
}
PARSINLU_SENTIMENT = {"-3": "absent", "-2": "negative", "-1": "negative", "0": "neutral", "1": "positive", "2": "positive", "3": "mixed"}
PARS_ABSA_SENTIMENT = {"-1": "negative", "0": "neutral", "1": "positive"}


def normalize_key(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", value).strip()


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def download_source(source: dict[str, Any], raw_dir: Path) -> Path:
    path = raw_dir / source["filename"]
    if path.exists():
        if digest(path.read_bytes()) != source["sha256"]:
            raise ValueError(f"checksum mismatch for cached source {path.name}; remove it and retry")
        return path
    request = urllib.request.Request(source["url"], headers={"User-Agent": "SnappFood-CX-benchmark-preparation/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
    if digest(content) != source["sha256"]:
        raise ValueError(f"checksum mismatch for downloaded source {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)
    return path


def base_record(source: dict[str, Any], index: str, text: str, target: str, sentiment: str) -> dict[str, Any]:
    return {
        "example_id": f"{source['dataset']}:{source['split']}:{index}",
        "dataset": source["dataset"], "source_revision": source["revision"],
        "split": source["split"], "text": text, "target": target,
        "review_group_id": digest(normalize_key(text).encode()),
        "aspect": None, "sentiment": sentiment, "aspect_term_span": None,
        "task": "aspect_conditioned_sentiment", "label_source": "public_gold",
        "evaluation_domain": "out_of_domain", "taxonomy_eligible": False,
    }


def parse_parsinlu(source: dict[str, Any], path: Path) -> tuple[list[dict[str, Any]], Counter]:
    records = []
    excluded: Counter = Counter()
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        row = json.loads(line)
        label = str(row["label"])
        if label not in PARSINLU_SENTIMENT:
            raise ValueError(f"unknown ParsiNLU label at line {index}")
        target = row["aspect"]
        if target not in PARSINLU_ASPECTS:
            excluded[f"unmapped_aspect:{target}"] += 1
            continue
        record = base_record(source, str(row["guid"]), row["review"], target, PARSINLU_SENTIMENT[label])
        record.update(aspect=PARSINLU_ASPECTS[target], taxonomy_eligible=True)
        # ParsiNLU supplies a queried aspect and no evidence-span annotation.
        record["source_label"] = label
        records.append(record)
    return records, excluded


def parse_pars_absa(source: dict[str, Any], path: Path) -> tuple[list[dict[str, Any]], Counter]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if len(lines) % 3:
        raise ValueError("Pars-ABSA file must contain three lines per example")
    records = []
    excluded: Counter = Counter()
    for index in range(0, len(lines), 3):
        template, target, label = lines[index:index + 3]
        if template.count("$T$") != 1:
            excluded["invalid_target_placeholder"] += 1
            continue
        if not target or label not in PARS_ABSA_SENTIMENT:
            raise ValueError(f"invalid Pars-ABSA target/label at example {index // 3 + 1}")
        prefix, suffix = template.split("$T$")
        text = prefix + target + suffix
        record = base_record(source, str(index // 3 + 1), text, target, PARS_ABSA_SENTIMENT[label])
        record["aspect_term_span"] = {"start": len(prefix), "end": len(prefix) + len(target), "text": target}
        record["source_label"] = label
        record["aspect"] = PARS_ABSA_ASPECTS.get(normalize_key(target))
        record["taxonomy_eligible"] = record["aspect"] is not None
        # Retain generic targets for a separate target-sentiment task, not food issue F1.
        records.append(record)
    return records, excluded


def remove_leakage(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter]:
    """Keep evaluation text out of train, across targets and datasets alike."""
    priority = {"test": 0, "validation": 1, "train": 2}
    best_split: dict[str, int] = {}
    for record in records:
        key = record["review_group_id"]
        best_split[key] = min(best_split.get(key, 3), priority[record["split"]])
    out = []
    removed: Counter = Counter()
    seen: set[tuple] = set()
    for record in records:
        split = record["split"]
        if priority[split] != best_split[record["review_group_id"]]:
            removed[f"{record['dataset']}:{split}:text_overlap_with_higher_priority_split"] += 1
            continue
        key = (record["dataset"], split, record["review_group_id"], normalize_key(record["target"]), record["sentiment"])
        if key in seen:
            removed[f"{record['dataset']}:{split}:duplicate_example"] += 1
            continue
        seen.add(key)
        out.append(record)
    return out, removed


def prepare(lock_path: Path, data_dir: Path, report_path: Path, schema_path: Path) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    records = []
    source_results = []
    for source in lock["sources"]:
        path = download_source(source, data_dir / "raw")
        parser = parse_parsinlu if source["dataset"] == "parsinlu_food" else parse_pars_absa
        parsed, excluded = parser(source, path)
        records.extend(parsed)
        source_results.append({**source, "parsed_rows": len(parsed), "excluded": dict(excluded), "checksum_verified": True})
        LOG.info(json.dumps({"event": "source_prepared", "dataset": source["dataset"], "split": source["split"], "parsed_rows": len(parsed), "excluded_rows": sum(excluded.values())}))
    clean, removed = remove_leakage(records)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in clean:
        groups[record["dataset"], record["split"]].append(record)
    summaries = []
    review_summaries = []
    processed = data_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    for (dataset, split), rows in sorted(groups.items()):
        path = processed / f"{dataset}_{split}.jsonl"
        content = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
        path.write_text(content, encoding="utf-8")
        summaries.append({"dataset": dataset, "split": split, "rows": len(rows), "review_groups": len({r["review_group_id"] for r in rows}), "taxonomy_eligible_rows": sum(r["taxonomy_eligible"] for r in rows), "aspect_counts": dict(Counter(r["aspect"] for r in rows if r["taxonomy_eligible"])), "sentiment_counts": dict(Counter(r["sentiment"] for r in rows)), "aspect_term_span_rows": sum(r["aspect_term_span"] is not None for r in rows), "sha256": digest(content.encode())})
        if dataset == "parsinlu_food":
            # Presence is evaluated only for the three supported categories.
            # Preserve sentiment sets instead of inventing a single merged gold label.
            reviews: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                reviews[row["review_group_id"]].append(row)
            review_rows = []
            for rid, annotations in sorted(reviews.items()):
                sentiments: dict[str, set[str]] = defaultdict(set)
                for annotation in annotations:
                    if annotation["sentiment"] != "absent":
                        sentiments[annotation["aspect"]].add(annotation["sentiment"])
                review_rows.append({"review_id": f"{dataset}:{rid}", "text": annotations[0]["text"], "split": split, "evaluation_domain": "out_of_domain", "evaluated_aspects": sorted(set(PARSINLU_ASPECTS.values())), "gold_aspects": sorted(sentiments), "gold_sentiments": {a: sorted(v) for a,v in sorted(sentiments.items())}, "evidence_gold_available": False})
            review_content = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in review_rows)
            (processed / f"{dataset}_{split}_reviews.jsonl").write_text(review_content, encoding="utf-8")
            review_summaries.append({"split": split, "reviews": len(review_rows), "sha256": digest(review_content.encode())})
    eligible = {r["aspect"] for r in clean if r["taxonomy_eligible"]}
    all_aspects = ["taste_quality", "temperature", "packaging", "price_value", "delivery_delay", "courier_behavior", "portion_size", "missing_wrong_items"]
    report = {
        "schema_version": "1.0", "evaluation_domain": "out_of_domain",
        "source_lock_sha256": digest(lock_path.read_bytes()), "sources": source_results,
        "runtime_versions": {"package": version("snappfood-cx-feasibility"), "pydantic": version("pydantic")},
        "prepared": summaries, "leakage_and_duplicates_removed": dict(removed),
        "parsinlu_review_level": review_summaries,
        "total_prepared_rows": len(clean), "taxonomy_covered": sorted(eligible),
        "taxonomy_without_gold_coverage": [a for a in all_aspects if a not in eligible],
        "limitations": ["No benchmark score is SnappFood accuracy.", "ParsiNLU absent is not neutral and its queried aspect has no evidence-span gold.", "Pars-ABSA spans mark aspect terms, not supporting opinion spans.", "Only exact curated general-product targets are mapped to the food taxonomy.", "No model was trained or evaluated in preparation; F1 and inference cost are not measured."],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(ReviewExtraction.model_json_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=Path("configs/benchmarks.lock.json"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/benchmarks"))
    parser.add_argument("--report", type=Path, default=Path("reports/benchmark_preparation.json"))
    parser.add_argument("--schema", type=Path, default=Path("schemas/extraction.schema.json"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    report = prepare(args.lock, args.data_dir, args.report, args.schema)
    LOG.info(json.dumps({"event": "preparation_complete", "rows": report["total_prepared_rows"]}))


if __name__ == "__main__":
    main()
