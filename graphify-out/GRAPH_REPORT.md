# Graph Report - snapfood_sentiment  (2026-10-20)

## Corpus Check
- 35 files · ~12,330 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 3, .csv 3, .lock 1)

## Summary
- 200 nodes · 449 edges · 9 communities (7 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ac8ebfe4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- sampling.py
- common.py
- snappfood-cx-feasibility
- benchmarks.py
- inference.py
- README.md
- SnappFood Customer Experience Intelligence — data feasibility study
- AGENTS.md
- pilot.py

## God Nodes (most connected - your core abstractions)
1. `save_json()` - 14 edges
2. `load_inventory()` - 13 edges
3. `configure()` - 12 edges
4. `run()` - 12 edges
5. `relation()` - 10 edges
6. `prepare()` - 10 edges
7. `prepare_sample()` - 10 edges
8. `main()` - 9 edges
9. `main()` - 9 edges
10. `validate_extraction()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `قرارداد استخراج` --references--> `validate_extraction()`  [INFERRED]
  docs/BENCHMARKS.md → src/snappfood_cx/contracts.py
- `Dataset inventory` --references--> `source()`  [INFERRED]
  docs/DATASET_INVENTORY.md → tests/test_benchmark_preparation.py
- `test_sampling_is_deterministic_and_order_independent()` --calls--> `sample_sql()`  [INFERRED]
  tests/test_audit_logic.py → scripts/common.py
- `test_adapter_rejection_codes_do_not_publish_customer_text()` --uses--> `OutputRejected`  [INFERRED]
  tests/test_pilot.py → src/snappfood_cx/inference.py
- `test_join_coverage_denominator()` --calls--> `join_coverage()`  [INFERRED]
  tests/test_audit_logic.py → scripts/analyze_relationships.py

## Import Cycles
- None detected.

## Communities (9 total, 2 thin omitted)

### Community 1 - "sampling.py"
Cohesion: 0.13
Nodes (13): allocate_strata(), attach_source_views(), create_eligible_view(), main(), prepare_sample(), select_sample(), proposed(), test_adapter_derives_offsets_without_rewriting_evidence() (+5 more)

### Community 2 - "common.py"
Cohesion: 0.11
Nodes (22): join_coverage(), main(), main(), parse_review_date(), candidate_aspects(), main(), duplicate_count(), main() (+14 more)

### Community 7 - "benchmarks.py"
Cohesion: 0.16
Nodes (20): base_record(), digest(), download_source(), main(), normalize_key(), parse_pars_absa(), parse_parsinlu(), prepare() (+12 more)

### Community 9 - "inference.py"
Cohesion: 0.11
Nodes (14): ContractModel, EvidenceSpan, ExtractionRecord, ReviewExtraction, validate_extraction(), build_messages(), ExtractionBackend, json_object_complete() (+6 more)

### Community 10 - "README.md"
Cohesion: 0.06
Nodes (24): Architecture proposal, اجرا و نگهداری, قرارداد استخراج, مرحلهٔ اول: قرارداد خروجی و دادهٔ ارزیابی, منابع ثابت و تبدیل برچسب‌ها, نتایج آماده‌سازی واقعی, Data quality report, Dataset inventory (+16 more)

### Community 12 - "SnappFood Customer Experience Intelligence — data feasibility study"
Cohesion: 0.29
Nodes (7): Graphify for coding assistants, Milestone 1: extraction contract and evaluation data, Milestone 2: local extraction pilot, Reports, Results, Setup and reproduction, SnappFood Customer Experience Intelligence — data feasibility study

### Community 19 - "pilot.py"
Cohesion: 0.17
Nodes (8): convert_response(), LocalTransformersBackend, OutputRejected, load_checkpoint(), main(), run(), sha(), summarize()

## Knowledge Gaps
- **1 isolated node(s):** `snappfood-cx-feasibility`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 59 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `source()` connect `benchmarks.py` to `README.md`?**
  _High betweenness centrality (0.205) - this node is a cross-community bridge._
- **What connects `snappfood-cx-feasibility` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `sampling.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13438735177865613 - nodes in this community are weakly interconnected._
- **Why does `Dataset inventory` connect `README.md` to `benchmarks.py`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Should `common.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10775510204081633 - nodes in this community are weakly interconnected._
- **Why does `validate_extraction()` connect `inference.py` to `README.md`, `pilot.py`, `benchmarks.py`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Should `inference.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10582010582010581 - nodes in this community are weakly interconnected._