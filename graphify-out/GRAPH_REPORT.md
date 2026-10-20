# Graph Report - snapfood_sentiment  (2026-10-20)

## Corpus Check
- 28 files · ~9,264 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: .csv 3, (none) 2, .lock 1)

## Summary
- 141 nodes · 304 edges · 20 communities (11 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c914c596`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- save_json
- common.py
- audit_data_quality.py
- analyze_temporal.py
- analyze_text.py
- load_inventory
- snappfood-cx-feasibility
- benchmarks.py
- json
- contracts.py
- README.md
- نقشهٔ راه پروژهٔ SnappFood Customer Experience Intelligence
- SnappFood Customer Experience Intelligence — data feasibility study
- مرحلهٔ اول: قرارداد خروجی و دادهٔ ارزیابی
- DATASET_INVENTORY.md
- AGENTS.md
- DATA_QUALITY_REPORT.md
- MODEL_STRATEGY.md
- NLP_FEASIBILITY.md

## God Nodes (most connected - your core abstractions)
1. `save_json()` - 14 edges
2. `load_inventory()` - 13 edges
3. `configure()` - 12 edges
4. `relation()` - 10 edges
5. `prepare()` - 10 edges
6. `main()` - 9 edges
7. `main()` - 9 edges
8. `main()` - 8 edges
9. `main()` - 8 edges
10. `parse_pars_absa()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `قرارداد استخراج` --references--> `validate_extraction()`  [INFERRED]
  docs/BENCHMARKS.md → src/snappfood_cx/contracts.py
- `Dataset inventory` --references--> `source()`  [INFERRED]
  docs/DATASET_INVENTORY.md → tests/test_benchmark_preparation.py
- `test_join_coverage_denominator()` --calls--> `join_coverage()`  [INFERRED]
  tests/test_audit_logic.py → scripts/analyze_relationships.py
- `test_sampling_is_deterministic_and_order_independent()` --calls--> `sample_sql()`  [INFERRED]
  tests/test_audit_logic.py → scripts/common.py
- `test_jalali_date_validation()` --calls--> `parse_review_date()`  [INFERRED]
  tests/test_audit_logic.py → scripts/analyze_temporal.py

## Import Cycles
- None detected.

## Communities (20 total, 9 thin omitted)

### Community 0 - "save_json"
Cohesion: 0.39
Nodes (4): metadata(), paths(), save_json(), main()

### Community 2 - "audit_data_quality.py"
Cohesion: 0.22
Nodes (8): duplicate_count(), main(), normalized_text(), text_features(), sample_sql(), test_duplicate_and_normalization(), test_join_coverage_denominator(), test_sampling_is_deterministic_and_order_independent()

### Community 3 - "analyze_temporal.py"
Cohesion: 0.27
Nodes (4): main(), parse_review_date(), relation(), test_jalali_date_validation()

### Community 4 - "analyze_text.py"
Cohesion: 0.53
Nodes (3): candidate_aspects(), main(), configure()

### Community 7 - "benchmarks.py"
Cohesion: 0.23
Nodes (9): base_record(), digest(), download_source(), main(), normalize_key(), parse_pars_absa(), parse_parsinlu(), prepare() (+1 more)

### Community 8 - "json"
Cohesion: 0.23
Nodes (12): validate_extraction(), payload(), source(), test_bad_cached_checksum_is_not_silently_replaced(), test_empty_extraction_is_valid(), test_evidence_validation_uses_original_unicode_offsets(), test_hardware_quality_is_not_food_quality(), test_invalid_model_output_rejected() (+4 more)

### Community 9 - "contracts.py"
Cohesion: 0.24
Nodes (4): ContractModel, EvidenceSpan, ExtractionRecord, ReviewExtraction

### Community 10 - "README.md"
Cohesion: 0.28
Nodes (3): Architecture proposal, Feasibility decision, Temporal and statistical feasibility

### Community 11 - "نقشهٔ راه پروژهٔ SnappFood Customer Experience Intelligence"
Cohesion: 0.33
Nodes (6): آزمون و فرض‌ها, قراردادها و تحویل‌دادنی‌ها, مراحل اجرا, نقشهٔ راه پروژهٔ SnappFood Customer Experience Intelligence, هدف و نقطهٔ شروع, وضعیت

### Community 12 - "SnappFood Customer Experience Intelligence — data feasibility study"
Cohesion: 0.33
Nodes (6): Graphify for coding assistants, Milestone 1: extraction contract and evaluation data, Reports, Results, Setup and reproduction, SnappFood Customer Experience Intelligence — data feasibility study

### Community 13 - "مرحلهٔ اول: قرارداد خروجی و دادهٔ ارزیابی"
Cohesion: 0.40
Nodes (5): اجرا و نگهداری, قرارداد استخراج, مرحلهٔ اول: قرارداد خروجی و دادهٔ ارزیابی, منابع ثابت و تبدیل برچسب‌ها, نتایج آماده‌سازی واقعی

## Knowledge Gaps
- **1 isolated node(s):** `snappfood-cx-feasibility`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 45 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `source()` connect `json` to `DATASET_INVENTORY.md`?**
  _High betweenness centrality (0.252) - this node is a cross-community bridge._
- **What connects `snappfood-cx-feasibility` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `Dataset inventory` connect `DATASET_INVENTORY.md` to `json`?**
  _High betweenness centrality (0.244) - this node is a cross-community bridge._
- **Why does `validate_extraction()` connect `json` to `contracts.py`, `مرحلهٔ اول: قرارداد خروجی و دادهٔ ارزیابی`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._