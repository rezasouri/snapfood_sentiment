"""Shared, bounded data access and deterministic audit helpers."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import duckdb
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("snappfood-reviews", "snappfood-review-replies", "snappfood-menus", "snappfood-vendors")
LOG = logging.getLogger("snappfood_audit")


def configure() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')


def metadata() -> dict[str, dict[str, Any]]:
    api = HfApi()
    out = {}
    for name in NAMES:
        info = api.dataset_info(f"EhsanShahbazi/{name}", files_metadata=True)
        card = info.card_data.to_dict() if info.card_data else {}
        out[name] = {
            "repo": f"EhsanShahbazi/{name}", "revision": info.sha,
            "gated": info.gated, "private": info.private,
            "license": card.get("license"),
            "dataset_info": card.get("dataset_info", {}),
            "files": [{"name": s.rfilename, "size_bytes": s.size} for s in info.siblings if s.rfilename.endswith(".parquet")],
            "basis": "repository_metadata",
        }
    return out


def paths(item: dict[str, Any]) -> list[str]:
    return [hf_hub_download(repo_id=item["repo"], repo_type="dataset", revision=item["revision"], filename=f["name"]) for f in item["files"]]


def relation(con: duckdb.DuckDBPyConnection, files: list[str], name: str) -> None:
    con.from_parquet(files).create_view(name, replace=True)


def sample_sql(table: str, n: int, seed: int) -> str:
    if n <= 0 or seed < 0:
        raise ValueError("sample size must be positive and seed nonnegative")
    # Stable across scans and independent of input row order; ties are broken by row text.
    return f"SELECT * FROM {table} ORDER BY hash(CAST(id AS VARCHAR) || '|' || CAST({seed} AS VARCHAR)), id LIMIT {n}"


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_inventory() -> dict[str, dict[str, Any]]:
    """Ensure pinned, locally accessible Parquet files before an independent audit."""
    path = ROOT / "reports" / "inventory.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if all(item.get("access") == "records_accessible" and all(Path(p).exists() for p in item.get("local_files", [])) for item in data.values()):
            return data
    subprocess.run([sys.executable, str(ROOT / "scripts" / "inspect_datasets.py")], check=True)
    return json.loads(path.read_text(encoding="utf-8"))
