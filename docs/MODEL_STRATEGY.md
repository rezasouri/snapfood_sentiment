# Model strategy

No model was trained or paid API called in this study. Current provider pricing and throughput were not verified.

| Approach | Strength | Limitation | Feasibility role |
|---|---|---|---|
| TF-IDF + linear multi-label models | Cheap, fast, interpretable baseline | Weak on implicit aspects, mixed sentiment, evidence spans | Baseline on public gold benchmarks and silver labels |
| Small Persian/multilingual transformer | Better contextual handling; locally deployable | Annotation and inference cost; drift | Candidate student model |
| API LLM structured extraction | Flexible taxonomy and evidence proposal | Cost, latency, prompt sensitivity, unsupported spans | Annotation assistant and bounded evaluation |
| LLM teacher + silver labels + student | Can scale after benchmark checks | Teacher errors can propagate; no in-domain accuracy guarantee | Optional staged strategy |

The project will not require new manual labels. First evaluate candidate extractors on existing Persian ABSA gold benchmarks, including the food-and-beverage subset of ParsiNLU. Then run a bounded SnappFood batch through a structured LLM or local model to propose multi-label aspects, sentiment and exact evidence spans. Reject invalid schemas, spans not present in the source, contradictory duplicate outputs and low-confidence cases. Store model/prompt versions and the silver-label source. Train a TF-IDF baseline and optionally one small transformer on silver labels; compare them with direct LLM extraction on the same external gold test set and a held-out SnappFood *silver* set. Report those two results separately; agreement with a teacher is not in-domain accuracy. Measure latency and cost before scaling. No paid API use is implied.

Colloquial Persian, mixed sentiment and 0 ratings make weak supervision from global labels risky. Normalize Persian characters while preserving original text and offsets for evidence. Provider adapters should expose one extraction interface and keep prompts/model versions in provenance.
