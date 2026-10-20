"""Pin dataset revisions and inspect metadata plus actual Parquet schema."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pyarrow.parquet as pq

from common import ROOT, configure, metadata, paths, save_json, LOG


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    configure()
    inventory = metadata()
    rows = []
    for name, item in inventory.items():
        item["access"] = "metadata_only"
        item["actual_rows_inspected"] = 0
        if not args.metadata_only:
            try:
                files = paths(item)
                item["local_files"] = files
                item["parquet_rows"] = sum(pq.ParquetFile(p).metadata.num_rows for p in files)
                item["parquet_schema"] = {f.name: str(f.type) for f in pq.ParquetFile(files[0]).schema_arrow}
                item["access"] = "records_accessible"
                LOG.info("%s: %s Parquet rows accessible", name, item["parquet_rows"])
            except Exception as exc:
                item["blocker"] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:180]}"
                LOG.warning("%s: %s", name, item["blocker"])
        rows.append({"dataset": name, "accessibility": item["access"], "metadata_rows": item["dataset_info"].get("splits", [{}])[0].get("num_examples"), "parquet_rows": item.get("parquet_rows"), "schema": "; ".join(f"{f['name']}:{f['dtype']}" for f in item["dataset_info"].get("features", [])), "candidate_keys": "id; see join report", "license": item["license"], "limitations": item.get("blocker", "relationships and field quality require audit"), "revision": item["revision"]})
    save_json(ROOT / "reports" / "inventory.json", inventory)
    with (ROOT / "reports" / "dataset_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
