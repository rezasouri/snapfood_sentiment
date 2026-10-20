import json
from pathlib import Path

import pytest

from snappfood_cx.benchmarks import (
    base_record, digest, download_source, parse_parsinlu, parse_pars_absa, prepare, remove_leakage,
)
from snappfood_cx.contracts import validate_extraction


def source(dataset="pars_absa", split="train"):
    return {"dataset": dataset, "split": split, "revision": "fixed-revision"}


def test_parsinlu_absence_is_preserved_and_shipping_not_delay(tmp_path):
    path = tmp_path / "food.jsonl"
    path.write_text("\n".join(json.dumps({"review": "نمونه", "aspect": aspect, "label": "-3", "guid": str(i)}) for i, aspect in enumerate(["طعم", "ارسال"])))
    rows, excluded = parse_parsinlu(source("parsinlu_food"), path)
    assert len(rows) == 1
    assert rows[0]["sentiment"] == "absent"
    assert rows[0]["aspect_term_span"] is None
    assert excluded["unmapped_aspect:ارسال"] == 1


def test_pars_target_offsets_and_malformed_templates(tmp_path):
    path = tmp_path / "pars.txt"
    path.write_text("این $T$ خوب است\nقیمت\n1\nبدون جایگزین\nکیفیت\n0\n", encoding="utf-8")
    rows, excluded = parse_pars_absa(source(), path)
    span = rows[0]["aspect_term_span"]
    assert rows[0]["text"][span["start"]:span["end"]] == "قیمت"
    assert rows[0]["aspect"] == "price_value"
    assert excluded["invalid_target_placeholder"] == 1


def test_hardware_quality_is_not_food_quality(tmp_path):
    path = tmp_path / "pars.txt"
    path.write_text("$T$ عالی\nکیفیت ساخت\n1\n", encoding="utf-8")
    rows, _ = parse_pars_absa(source(), path)
    assert not rows[0]["taxonomy_eligible"]


def test_split_leakage_removed_across_targets_and_sources():
    rows = [
        base_record(source(), "1", "متن یکسان", "قیمت", "positive"),
        base_record(source("parsinlu_food", "test"), "2", "متن یکسان", "طعم", "negative"),
        base_record(source(split="train"), "3", "متن متفاوت", "قیمت", "neutral"),
    ]
    clean, removed = remove_leakage(rows)
    assert [r["split"] for r in clean] == ["test", "train"]
    assert sum(removed.values()) == 1
    train = {r["review_group_id"] for r in clean if r["split"] == "train"}
    test = {r["review_group_id"] for r in clean if r["split"] == "test"}
    assert train.isdisjoint(test)


def test_bad_cached_checksum_is_not_silently_replaced(tmp_path):
    (tmp_path / "source.txt").write_text("corrupt")
    with pytest.raises(ValueError, match="checksum mismatch"):
        download_source({"filename": "source.txt", "sha256": "0" * 64}, tmp_path)


def payload():
    return {"review_id": "r1", "records": [{"review_id": "r1", "aspect": "temperature", "sentiment": "negative", "evidence_span": {"start": 0, "end": 7, "text": "غذا سرد"}, "label_source": "model_generated", "model_version": "test@revision"}]}


def test_evidence_validation_uses_original_unicode_offsets():
    result = validate_extraction(json.dumps(payload()), review_id="r1", original_text="غذا سرد بود")
    assert result.records[0].validation_status == "validated"


@pytest.mark.parametrize("change", ["review_id", "span", "aspect", "extra"])
def test_invalid_model_output_rejected(change):
    data = payload()
    if change == "review_id": data["records"][0]["review_id"] = "wrong"
    if change == "span": data["records"][0]["evidence_span"]["text"] = "غذای گرم"
    if change == "aspect": data["records"][0]["aspect"] = "invented"
    if change == "extra": data["private_field"] = "unexpected"
    with pytest.raises(ValueError):
        validate_extraction(json.dumps(data), review_id="r1", original_text="غذا سرد بود")


def test_empty_extraction_is_valid():
    result = validate_extraction('{"review_id":"r1","records":[]}', review_id="r1", original_text="سلام")
    assert result.records == []


def test_preparation_is_repeatable_and_preserves_merged_sentiments(tmp_path):
    data = tmp_path / "data"
    raw = data / "raw"
    raw.mkdir(parents=True)
    rows = [{"guid": str(i), "review": "کیفیت و طعم متفاوت", "aspect": aspect, "label": label} for i, (aspect, label) in enumerate([("طعم", "1"), ("کیفیت", "-1"), ("بسته بندی", "-3")])]
    content = "\n".join(json.dumps(row) for row in rows).encode()
    (raw / "food.jsonl").write_bytes(content)
    src = {**source("parsinlu_food"), "filename": "food.jsonl", "sha256": digest(content), "url": "https://unused.example", "license": "test-fixture"}
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({"sources": [src]}))
    args = (lock, data, tmp_path / "report.json", tmp_path / "schema.json")
    assert prepare(*args) == prepare(*args)
    records = [json.loads(line) for line in (data / "processed/parsinlu_food_train_reviews.jsonl").read_text().splitlines()]
    assert records[0]["gold_sentiments"] == {"taste_quality": ["negative", "positive"]}
    assert records[0]["gold_aspects"] == ["taste_quality"]
