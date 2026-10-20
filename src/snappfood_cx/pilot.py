"""Run resumable local extraction; publish aggregates, retain raw output locally."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import time
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from .inference import LocalTransformersBackend, OutputRejected, PROMPT_VERSION, PROMPT_EXAMPLES, SYSTEM_PROMPT, convert_response
from . import inference

LOG=logging.getLogger(__name__)


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_checkpoint(path: Path, signature: str) -> list[dict]:
    if not path.exists(): return []
    content=path.read_bytes()
    # A process killed mid-write may leave one incomplete final record.
    if content and not content.endswith(b"\n"):
        content=content[:content.rfind(b"\n")+1]
        path.write_bytes(content)
    rows=[json.loads(line) for line in content.splitlines()]
    if any(row.get("run_signature") != signature for row in rows):
        raise ValueError("checkpoint settings differ; choose a new output directory")
    if len({r["review_id"] for r in rows}) != len(rows):
        raise ValueError("checkpoint contains duplicate review IDs")
    return rows


def summarize(results: list[dict], sample_size: int, config: dict, signature: str, elapsed: float, sample_hash: str, peak_memory: int) -> dict:
    import torch
    accepted=[r for r in results if r["accepted"]]
    records=[record for r in accepted for record in r["extraction"]["records"]]
    return {
        "run_signature":signature,"sample_sha256":sample_hash,"sample_size":sample_size,
        "processed":len(results),"complete":len(results)==sample_size,
        "accepted_reviews":len(accepted),"rejected_reviews":len(results)-len(accepted),
        "valid_output_rate":len(accepted)/len(results) if results else None,
        "accepted_empty_reviews":sum(not r["extraction"]["records"] for r in accepted),
        "accepted_records":len(records),"rejection_reasons":dict(Counter(r["error"] for r in results if not r["accepted"])),
        "aspect_record_counts":dict(Counter(r["aspect"] for r in records)),
        "sentiment_record_counts":dict(Counter(r["sentiment"] for r in records)),
        "input_tokens":sum(r.get("input_tokens",0) for r in results),
        "output_tokens":sum(r.get("output_tokens",0) for r in results),
        "accumulated_batch_seconds":sum(r["allocated_batch_seconds"] for r in results),
        "latest_invocation_seconds":elapsed,"peak_cuda_allocated_bytes":max([peak_memory]+[r.get("peak_cuda_allocated_bytes",0) for r in results]),
        "model":config,"prompt_version":PROMPT_VERSION,"prompt_sha256":sha(json.dumps({"system":SYSTEM_PROMPT,"examples":PROMPT_EXAMPLES},ensure_ascii=False,sort_keys=True).encode()),
        "adapter_sha256":sha(Path(inference.__file__).read_bytes()),
        "device_name":torch.cuda.get_device_name() if torch.cuda.is_available() else "unavailable",
        "semantic_accuracy":None,"quality_gate_status":"not_evaluated",
        "versions":{p:version(p) for p in ("torch","transformers","pydantic","duckdb")},
        "interpretation":"Validity is JSON/ID/exact-evidence validation, not aspect or sentiment accuracy. Counts are pilot outputs, not population issue rates.",
    }


def run(sample_path: Path, config_path: Path, output_dir: Path, report_path: Path, limit: int | None) -> dict:
    import torch

    started=time.perf_counter()
    content=sample_path.read_bytes()
    samples=[json.loads(line) for line in content.splitlines()]
    if not samples:
        raise ValueError("sample must not be empty")
    if len({r["review_id"] for r in samples}) != len(samples):
        raise ValueError("sample contains duplicate review IDs")
    config=json.loads(config_path.read_text())
    if config["batch_size"] <= 0 or config["max_new_tokens"] <= 0 or config["max_input_tokens"] <= 0:
        raise ValueError("model size limits must be positive")
    if config["dtype"] != "float16" or config["enable_thinking"] or config["do_sample"]:
        raise ValueError("this adapter requires float16, non-thinking, greedy inference")
    sample_hash=sha(content)
    adapter_hash=sha(Path(inference.__file__).read_bytes())
    signature=sha(json.dumps({"sample":sample_hash,"config":config,"prompt":SYSTEM_PROMPT,"adapter_sha256":adapter_hash},sort_keys=True).encode())
    output_dir.mkdir(parents=True,exist_ok=True)
    result_path=output_dir/"results.jsonl"
    results=load_checkpoint(result_path,signature)
    known={r["review_id"] for r in samples}
    if any(r["review_id"] not in known for r in results): raise ValueError("checkpoint contains unknown review ID")
    done={r["review_id"] for r in results}
    pending=sorted((r for r in samples if r["review_id"] not in done),key=lambda r:(len(r["text"]),r["review_id"]))
    if limit is not None:
        if limit <= 0: raise ValueError("limit must be positive")
        pending=pending[:max(0,limit-len(results))]
    backend=LocalTransformersBackend(config) if pending else None
    output_dir.joinpath("run.json").write_text(json.dumps({"run_signature":signature,"sample_sha256":sample_hash,"adapter_sha256":adapter_hash,"model":config,"prompt_version":PROMPT_VERSION},indent=2)+"\n")
    batch_size=config["batch_size"]
    for offset in range(0,len(pending),batch_size):
        batch=pending[offset:offset+batch_size]
        torch.cuda.synchronize()
        before=time.perf_counter()
        outputs=backend.generate(batch)
        torch.cuda.synchronize()
        seconds=time.perf_counter()-before
        if len(outputs) != len(batch): raise ValueError("backend returned the wrong output count")
        with result_path.open("a",encoding="utf-8") as stream:
            for review,output in zip(batch,outputs):
                result={"review_id":review["review_id"],"run_signature":signature,"raw_output":output["raw"],"input_tokens":output["input_tokens"],"output_tokens":output["output_tokens"],"allocated_batch_seconds":seconds/len(batch),"peak_cuda_allocated_bytes":torch.cuda.max_memory_allocated(),"accepted":False,"error":None}
                try:
                    if output.get("error"): raise OutputRejected(output["error"])
                    if output["truncated"]: raise OutputRejected("output_truncated")
                    extraction=convert_response(output["raw"],review["review_id"],review["text"],backend.model_version)
                    result.update(accepted=True,extraction=extraction.model_dump())
                except OutputRejected as exc:
                    result["error"]=str(exc)
                stream.write(json.dumps(result,ensure_ascii=False)+"\n")
                results.append(result)
            stream.flush();os.fsync(stream.fileno())
        peak=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
        report=summarize(results,len(samples),config,signature,time.perf_counter()-started,sample_hash,peak)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        LOG.info(json.dumps({"event":"batch_complete","processed":len(results),"total":len(samples),"accepted":report["accepted_reviews"],"seconds":round(seconds,2)}))
    peak=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
    report=summarize(results,len(samples),config,signature,time.perf_counter()-started,sample_hash,peak)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    previous=json.loads(report_path.read_text()) if report_path.exists() else {}
    if not pending and previous.get("run_signature") == signature:
        report["last_inference_invocation_seconds"]=previous.get("last_inference_invocation_seconds",previous.get("latest_invocation_seconds"))
    else:
        report["last_inference_invocation_seconds"]=report["latest_invocation_seconds"]
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    accepted_content="".join(json.dumps(r["extraction"],ensure_ascii=False)+"\n" for r in results if r["accepted"])
    output_dir.joinpath("extractions.jsonl").write_text(accepted_content,encoding="utf-8")
    return report


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample",type=Path,default=Path("data/pilot/reviews.jsonl"))
    p.add_argument("--model-config",type=Path,default=Path("configs/pilot.model.json"))
    p.add_argument("--output-dir",type=Path,default=Path("data/pilot/qwen3-v3"))
    p.add_argument("--report",type=Path,default=Path("reports/pilot_extraction.json"))
    p.add_argument("--limit",type=int)
    args=p.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(message)s")
    report=run(args.sample,args.model_config,args.output_dir,args.report,args.limit)
    print(json.dumps({"event":"pilot_finished","processed":report["processed"],"complete":report["complete"]}))


if __name__ == "__main__":main()
