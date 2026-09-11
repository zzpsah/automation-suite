"""Build a normalized training corpus from reviewed OCR examples.

Input JSONL records may contain raw OCR, corrected text, and metadata. The
collector intentionally writes only the fields needed for learning and strips
empty examples. It never mutates the runtime language pack.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def collect_records(paths: Iterable[str]) -> list[dict]:
    records: list[dict] = []
    for filename in paths:
        for line in Path(filename).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            corrected = str(row.get("corrected_text", "")).strip()
            if not corrected:
                continue
            records.append({
                "id": row.get("id"),
                "language": row.get("language", "hi"),
                "raw_text": str(row.get("raw_text", "")),
                "corrected_text": corrected,
                "metadata": row.get("metadata", {}),
                "source": row.get("source", "reviewed"),
            })
    return records


def write_jsonl(records: Iterable[dict], output: str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
