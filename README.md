# SnappFood Customer Experience Intelligence — data feasibility study

Project roadmap: [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).

## Milestone 1: extraction contract and evaluation data

Implemented the eight-aspect extraction contract, exact evidence-span validation, and pinned public benchmark preparation. Preparation produced 15,509 target/aspect-conditioned examples after excluding invalid rows, duplicate examples, and train/test text overlap. These benchmarks cover three project aspects; they do not establish SnappFood accuracy. See [the preparation report and limitations](docs/BENCHMARKS.md).

```bash
uv sync --extra dev --locked
uv run snappfood-prepare-benchmarks
uv run pytest -q
```

Raw and processed benchmark text stays under ignored `data/benchmarks/`. Source revisions/checksums are pinned in `configs/benchmarks.lock.json`; the extraction JSON Schema is in `schemas/extraction.schema.json`. No model training or inference occurs in this milestone.

## Milestone 2: local extraction pilot

Milestone 2: [local extraction pilot](docs/LOCAL_PILOT.md) adds deterministic sampling, a pinned local model adapter, exact evidence validation, and resumable processing. Run `uv sync --extra dev --extra inference --locked`, then `uv run --extra inference snappfood-sample-reviews` and `uv run --extra inference snappfood-run-pilot`. Review text and raw inference output remain in ignored `data/pilot/`; published reports contain aggregate metrics only.

The actual 1,000-review run accepted 884 structurally grounded outputs (332 empty, 552 nonempty) containing 986 proposed aspect/sentiment records, and rejected 116. Inference batches took 751.7 seconds on the local RTX 3050; peak CUDA allocation was 4.45 GiB. These are pipeline-validity metrics, **not ABSA accuracy**. The quality gate is still `not_evaluated`. See [sampling](reports/pilot_sample.json) and [extraction metrics](reports/pilot_extraction.json).

## Graphify for coding assistants

This repository includes a project-scoped Graphify skill in `.codex/skills/graphify/`, Codex guidance in `AGENTS.md`, and a local code graph in `graphify-out/`. The graph currently indexes source code and tests; document semantics were skipped to avoid an external LLM call. The `.graphifyignore` file excludes `.env`, cached data, reports containing local details, and the old notebook.

Install the CLI with `uv tool install graphifyy==0.9.92`. From this directory, run `graphify query "How does the data audit work?"` to navigate the graph. After code changes, run `graphify update .`; after larger structural changes, run `graphify extract . --code-only` followed by `graphify cluster-only .`. The generated graph can be read by Codex via the installed project skill. No hosted Graphify account is required.

This repository audits whether four public gated SnappFood datasets can support an evidence-grounded customer-experience portfolio project. The study uses **actual Parquet records** and does not train models or call paid LLM APIs.

## Results

At pinned revisions, the audit accessed 6,536,959 reviews, 2,356,705 replies, 2,104,473 menu rows and 42,249 vendors. All reply→review and menu→vendor identifiers matched. A strict same-row menu `id`+`alias` match maps 6,396,964 reviews (97.8584%) to an item; a conservative item-or-unique-alias rule maps 6,500,837 (99.4474%) to a vendor. Review dates parse as Jalali, but the dataset is one historical collection snapshot. Under the no-manual-labeling constraint, ABSA uses external Persian gold benchmarks and generated silver labels; SnappFood accuracy remains unverified. Decision: **Conditional Go** for vendor-level issue intelligence; see [decision](docs/FEASIBILITY_DECISION.md).

## Setup and reproduction

Python 3.10+ and about 1 GB of disk cache are needed. `uv` is preferred:

```bash
uv sync --extra dev
hf auth login
uv run python scripts/inspect_datasets.py
uv run python scripts/audit_data_quality.py --sample-size 20000 --seed 42
uv run python scripts/analyze_relationships.py
uv run python scripts/analyze_text.py --sample-size 20000 --seed 42
uv run python scripts/analyze_temporal.py
uv run pytest -q
```

Without `uv`, use `python -m pip install -e '.[dev]'` and replace `uv run` with `python` or `pytest`. Hugging Face repositories are `gated: auto`; authenticated access is required. Use `hf auth login` locally. Keep tokens out of `.env` in Git and out of logs. The scripts download pinned Parquet shards to the Hugging Face cache, scan columns with DuckDB and store only aggregate reports. Change `--sample-size` and `--seed` to rerun bounded text audits. In this run: DuckDB 1.5.6, PyArrow 25.0.1, huggingface-hub 1.17.0, jdatetime 6.1.1, pytest 9.1.1.

If access is blocked, run `python scripts/inspect_datasets.py --metadata-only`; the inventory will distinguish card metadata from actual-record verification. After access is granted, rerun the full sequence above. Analysis scripts read the inventory produced by `inspect_datasets.py`.

## Reports

- [Dataset inventory](docs/DATASET_INVENTORY.md) and [CSV](reports/dataset_inventory.csv)
- [Data quality](docs/DATA_QUALITY_REPORT.md) and [metrics JSON](reports/metrics.json)
- [Relational feasibility](docs/RELATIONAL_FEASIBILITY.md) and [join CSV](reports/join_analysis.csv)
- [NLP feasibility](docs/NLP_FEASIBILITY.md)
- [Temporal feasibility](docs/TEMPORAL_FEASIBILITY.md)
- [Model strategy](docs/MODEL_STRATEGY.md)
- [Architecture](docs/ARCHITECTURE_PROPOSAL.md)
- [Decision](docs/FEASIBILITY_DECISION.md) and [matrix CSV](reports/feasibility_matrix.csv)

The report distinguishes full scans, deterministic samples, repository metadata and unverified hypotheses. No raw review text, sender names, vendor contacts or credentials are committed. Main limits: historical vendor/item identity may change, most items have sparse reviews, no order denominator, no in-domain aspect gold labels, and unknown collection completeness.
