from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common import sample_sql
from audit_data_quality import duplicate_count, normalized_text
from analyze_relationships import join_coverage
from analyze_temporal import parse_review_date


def test_sampling_is_deterministic_and_order_independent():
    import duckdb
    c = duckdb.connect()
    c.sql("CREATE TABLE a AS SELECT * FROM (VALUES (3),(1),(2)) t(id)")
    c.sql("CREATE TABLE b AS SELECT * FROM (VALUES (2),(3),(1)) t(id)")
    for seed in (1, 42):
        a = c.sql(sample_sql("a", 2, seed)).fetchall()
        b = c.sql(sample_sql("b", 2, seed)).fetchall()
        assert a == b


def test_jalali_date_validation():
    assert str(parse_review_date("۱۴۰۴/۱۰/۱۲")) == "2026-01-02"
    assert parse_review_date("۱۴۰۴/۱۳/۰۱") is None
    assert parse_review_date("2026-01-02") is None
    assert parse_review_date(None) is None


def test_duplicate_and_normalization():
    assert duplicate_count([1, 1, 2]) == 1
    assert normalized_text("عالي!!!") == normalized_text("عالی")


def test_join_coverage_denominator():
    assert join_coverage(10, 7) == 0.7
    assert join_coverage(0, 0) == 0.0
