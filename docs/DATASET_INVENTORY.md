# Dataset inventory

Audited 2026-10-13 (Asia/Tehran). Sources are the four repositories in the [Snappfood collection](https://huggingface.co/collections/EhsanShahbazi/snappfood-dataset). All are `gated: auto`; authenticated access succeeded. Repository cards state MIT. This is publisher metadata, not an independent legal review.

| Dataset | Rows in actual Parquet | Revision | Candidate keys | Main fields | Limitations |
|---|---:|---|---|---|---|
| [Reviews](https://huggingface.co/datasets/EhsanShahbazi/snappfood-reviews) | 6,536,959 | `6091ba922cfbefec842e578e7768d0392d876782` | `id` unique; `product_alias` links to menu with validation | `id`, `product_alias`, `sender`, `date`, `feeling`, `rate`, `rating`, `comment_text`, `fetched_at` | No direct vendor ID; `sender` may identify people; dates are Jalali text |
| [Replies](https://huggingface.co/datasets/EhsanShahbazi/snappfood-review-replies) | 2,356,705 | `9d6547e017f803065a62dcee88c66735615af2ad` | `id` unique; `review_id` candidate link | `id`, `review_id`, `source`, `comment_text`, `date` | Text may contain personal details; no reply outcome labels |
| [Menus](https://huggingface.co/datasets/EhsanShahbazi/snappfood-menus) | 2,104,473 | `b2ec1e694d4a30c2f5ffb0be3b45f0fd3b602eb7` | `id` unique; `alias` repeats; `vendor_code` candidate link | item/title, alias, vendor code, price, rating | No item history or date; alias is not a unique item key |
| [Vendors](https://huggingface.co/datasets/EhsanShahbazi/snappfood-vendors) | 42,249 | `a3d53011c3012e53a0c715bb11791e5fdb068e42` | `id` and `vendorCode` unique | vendor, location, delivery and rating fields | Snapshot fields; address, phone and coordinates require care |

Rows and schemas above were verified from downloaded Parquet metadata. Licenses, revisions and gated status were verified from repository metadata. Primary/foreign key declarations were **not** provided by the cards; relationships were measured against records in [RELATIONAL_FEASIBILITY.md](RELATIONAL_FEASIBILITY.md). No actual customer text or contact data is published here. Complete field types and access status are in [`reports/dataset_inventory.csv`](../reports/dataset_inventory.csv).
