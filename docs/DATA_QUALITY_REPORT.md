# Data quality report

Run: `python scripts/audit_data_quality.py --sample-size 20000 --seed 42`. Null/empty counts, IDs, exact text duplicates and rating distributions cover **all records**. Language and text-length indicators use the lowest 20,000 stable ID hashes per text dataset, not a handpicked sample. Full machine-readable metrics: [`reports/metrics.json`](../reports/metrics.json).

| Metric | Reviews (6,536,959) | Replies (2,356,705) | Scope |
|---|---:|---:|---|
| Duplicate IDs | 0 | 0 | Full |
| Exact duplicate text rows beyond first occurrence | 1,891,993 | 1,071,497 | Full |
| Null/empty text | 0 / 0 | 0 / 0 | Full |
| Reviews with fewer than 5 characters | 290,287 | — | Full |
| Normalized duplicate rows | 3,911 / 20,000 | 5,507 / 20,000 | Sample proxy; Persian character and punctuation normalization |
| Persian-script text | 19,958 / 20,000 | 19,988 / 20,000 | Sample; script presence, not language identification |
| Latin-script text | 54 / 20,000 | 375 / 20,000 | Sample; may coexist with Persian |
| Median words | 8 | 10 | Sample |
| Fewer than 4 words | 4,542 / 20,000 | 3,497 / 20,000 | Sample |

Review text sample character quantiles: p10 10, p50 40, p90 128, p99 273. Arabic `ي` appears in 632/20,000 reviews and Arabic `ك` in 355/20,000; normalization is needed. Zero-width non-joiner occurs in 931/20,000. The simple sample regex found no emoji, URLs or HTML in review text; this is not a guarantee for all rows. Normalized duplicate count is a *near-duplicate proxy*, not a semantic duplicate estimate.

All review `rate` and `rating` values are identical (0 disagreements). Their distribution is 10: 3,909,375; 8: 829,938; 6: 628,823; 4: 304,398; 2: 666,144; 0: 198,280; 20: 1. The 20 is outside the apparent 0–10 scale. Zero may represent missing/unrated: it coexists with HAPPY (139,151), SAD (48,062), NOTHING (8,903) and empty feeling (2,164); its meaning is undocumented. `feeling` is overwhelmingly HAPPY (5,507,291) versus SAD (1,018,601), with 8,903 NOTHING and 2,164 empty. Thus rating and sentiment are biased/derived signals and are unsuitable as unquestioned aspect-level truth. A manually inspected deterministic subset showed mixed opinions inside HAPPY reviews and a negative text inside a HAPPY review rated 6.

In the 20,000-review sample, 1,125 HAPPY texts contained an explicit complaint-term candidate and 330 SAD texts contained a praise-term candidate. These are **screening counts**, not confirmed contradictions: multi-aspect comments can legitimately contain both views. Human review is required to estimate label error.

Other gaps: 4,532 empty review `sender` values and 2,164 empty `feeling` values; no null review ID/date/rating/text. Menu descriptions are empty in 268,209 rows, images in 420,155, titles in 72. Vendor addresses/phones/coordinates exist; 34,436 vendor phone fields and all 42,249 website fields are empty. Reports omit these values.

Potential personal data: review sender names, free-text contacts, reply text, vendor addresses/phone and precise coordinates. Raw Parquet remains in the Hugging Face cache; `.env`, raw data and Parquet files are ignored by Git. Public excerpts require redaction and privacy review.
