"""Offline OCR improvement pipeline: collect → mine → evaluate → report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidate_miner import mine_token_corrections
from .collector import collect_records


def run(inputs: list[str], output_dir: str) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records = collect_records(inputs)
    candidates = mine_token_corrections(records)
    (out / "correction_candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report = {
        "records": len(records),
        "candidate_corrections": len(candidates),
        "status": "review-required",
        "runtime_files_modified": False,
    }
    (out / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Reviewed JSONL files")
    parser.add_argument("--output-dir", default="training_artifacts")
    args = parser.parse_args()
    print(json.dumps(run(args.inputs, args.output_dir), ensure_ascii=False))
