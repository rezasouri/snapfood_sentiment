# Relational feasibility

All counts are exact full-dataset joins, computed by [`scripts/analyze_relationships.py`](../scripts/analyze_relationships.py). Details: [`reports/join_analysis.csv`](../reports/join_analysis.csv), [`reports/join_details.json`](../reports/join_details.json).

| Relationship | Matched / left rows | Result |
|---|---:|---|
| Reply `review_id` → review `id` | 2,356,705 / 2,356,705 | Exact, unambiguous; review IDs unique |
| Menu `vendor_code` → vendor `vendorCode` | 2,104,473 / 2,104,473 | Exact, unambiguous; vendor codes unique |
| Review `product_alias` → menu `alias` | 6,536,959 / 6,536,959 | Complete existence match; alias alone is ambiguous |
| Review `product_alias` → same-row menu `id` **and** `alias` | 6,396,964 / 6,536,959 | Exact, unique item mapping (97.8584%) |
| Review `product_alias` → vendor `vendorCode` directly | 0 / 6,536,959 | Unsupported direct join |

Menu `alias` has 1,408,550 distinct values across 2,104,473 rows. 70,345 aliases repeat; 62,983 map to multiple vendors. A naive review–menu join yields 6,656,650 rows, inflating counts. Using alias alone and requiring one vendor yields 6,462,466 vendor mappings (98.8604%); 74,493 reviews have multi-vendor aliases across 2,947 aliases.

A stronger item join requires `review.product_alias = CAST(menu.id AS VARCHAR) = menu.alias` **on the same menu row**. Because `menu.id` is unique, this maps 6,396,964 reviews to one item and vendor. Another 103,873 reviews lack that item match but have an alias with one vendor. Together these give a conservative 6,500,837 vendor mappings (99.4474%). The rest are 20,604 numeric `id` collisions where the matched row's `alias` differs, and 15,518 alias-only cases spanning vendors. We exclude both. A numeric `id` match alone is not reliable: 20,604 such matches conflict with the row alias. Reports publish aggregate counts rather than customer records.

This supports **vendor-level** analytics for the conservatively mapped subset and **item-level** analytics for the exact item subset. It does not prove historical ownership: menus and vendors are snapshots, while reviews span almost ten years. Alias reuse or changing menu assignments could misattribute old reviews. The source cards do not define foreign keys or validity periods. Approximate name/text joins should be kept separate from exact key coverage and are not accepted for production claims.

31,186 vendors have at least one conservatively mapped review; their median review count is 30 (p10 2, p90 514). Only 9,503 have at least 100 reviews over the whole period. This strongly limits fine-grained comparisons.

The exact item subset covers 452,302 distinct items. Median reviews per matched item is 4 (p90 31); only 47,557 items have at least 30 reviews over the entire period. Item-level trends will be sparse even when the key is valid.
