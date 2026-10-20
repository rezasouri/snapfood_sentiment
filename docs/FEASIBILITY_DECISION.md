# Feasibility decision

**Conditional Go** for a portfolio-grade, evidence-grounded **vendor-level review intelligence prototype**. Real records support large-scale review analysis, exact replies→reviews, menus→vendors and a conservative vendor mapping for 99.4474% of reviews. Exact item mapping is available for 97.8584%. With no manual SnappFood labeling, issue statistics are model estimates and in-domain ABSA accuracy remains unknown. Production readiness is conditional on historical key validation, privacy review, domain evaluation and temporal coverage checks. The public data alone cannot prove order-level complaint rates or intervention impact.

| Capability | Status | Required / available evidence | Missing dependency and risk | Evaluation / recommendation |
|---|---|---|---|---|
| Vendor-level analytics | CONDITIONALLY FEASIBLE | 6,500,837 conservative mappings | 36,122 excluded collisions/ambiguous reviews; no historical menu validity | Audit mappings by year |
| ABSA | CONDITIONALLY FEASIBLE | Rich Persian text; public Persian ABSA benchmarks | No in-domain gold aspect/span labels | External benchmark F1; label SnappFood results as estimates |
| Temporal review volume | FEASIBLE | All review dates parse; 118 months | Historical coverage unknown | Show denominators and missing-period caveat |
| Temporal issue trends | CONDITIONALLY FEASIBLE | Dates and vendor link | Needs issue labels; sparse vendor-month cells | ≥30 denominator; Wilson intervals |
| Anomaly detection | CONDITIONALLY FEASIBLE | Period counts exist | Labels, baseline, review selection bias | ≥100 denominator, backtest false alerts |
| Evidence-backed summaries | CONDITIONALLY FEASIBLE | Stable review IDs and text | Retrieval/citation faithfulness unmeasured | Human factuality and citation checks |
| Vendor action recommendations | CONDITIONALLY FEASIBLE | Issue summaries can support hypotheses | No intervention/outcome data | Human review; avoid causal wording |
| Issue severity/prioritization | CONDITIONALLY FEASIBLE | Text, ratings and frequencies | Human severity rubric; rating ≠ severity | Adjudicated agreement; transparent scoring |
| Cross-vendor comparisons | CONDITIONALLY FEASIBLE | 31,186 vendors with conservatively linked reviews | Exposure and review-selection bias | Stratify and show uncertainty |
| LLM-assisted annotation and model comparison | CONDITIONALLY FEASIBLE | Large text corpus; external gold benchmarks | In-domain gold and cost measurement | External gold test plus separate silver agreement |
| Production API/monitoring | CONDITIONALLY FEASIBLE | Stable IDs and aggregates | Privacy review and operational quality gates | Contract and observability checks |
| Reply generation | CONDITIONALLY FEASIBLE | 2,356,705 exact linked replies | No outcome or policy labels; privacy | Human approval and quality rubric; defer from MVP |
| Item-level analytics | CONDITIONALLY FEASIBLE | 6,396,964 exact same-row ID+alias matches | Sparse items; historical key validity unknown | Restrict to exact subset and audit by year |
| Order-level complaint rate / causal effect | NOT SUPPORTED | Reviews only | No orders, exposure or experiments | Remove from scope |

Machine-readable matrix: [`reports/feasibility_matrix.csv`](../reports/feasibility_matrix.csv). The recommended MVP is (1) a privacy-safe, pinned data pipeline; (2) high-confidence vendor mapping; (3) external-benchmark evaluation followed by silver-label extraction; (4) weekly/monthly *estimated* issue rates with sample sizes; (5) evidence IDs and validated summaries in a demo dashboard. Postpone sparse item trends, autonomous reply posting, causal recommendations, and real-time anomaly alerts. Do not advertise SnappFood ABSA accuracy or production-grade issue rates without an in-domain gold set.
