"""Regression gate for reviewed OCR metadata expectations."""
from __future__ import annotations

import json
from pathlib import Path

from ..sarkari_normalizer import extract_metadata


def load_cases(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def run(corpus_path: str) -> dict:
    cases = load_cases(corpus_path)
    failures = []
    for case in cases:
        actual = extract_metadata(case.get("text", "")).to_dict()
        for field, expected in case.get("expected", {}).items():
            if actual.get(field) != expected:
                failures.append({"case": case.get("name"), "field": field, "expected": expected, "actual": actual.get(field)})
    return {"cases": len(cases), "failures": failures, "passed": not failures}
