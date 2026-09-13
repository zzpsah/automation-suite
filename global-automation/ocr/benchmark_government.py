"""Field-level benchmark for Government Document Intelligence.

Ground-truth files contain expected metadata, not document text. This keeps the
benchmark corpus privacy-safe while measuring extraction quality field by field.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable

from .government_document import analyze_document

FIELDS = ("authority", "subject", "document_type", "short_description")


def _norm(value: Any) -> str:
    return " ".join(str(value or "").casefold().split()).strip(" .:-–—")


def _score(expected: Any, actual: Any) -> float:
    if expected is None or expected == "":
        return 1.0 if not actual else 0.0
    e, a = _norm(expected), _norm(actual)
    if not e:
        return 1.0
    if e == a:
        return 1.0
    if e in a or a in e:
        return 0.75
    # Token overlap is useful for multi-line summaries/subjects without making
    # near-matches indistinguishable from exact matches.
    et, at = set(e.split()), set(a.split())
    return round(len(et & at) / max(1, len(et)), 4)


@dataclass
class FieldScore:
    field: str
    expected: Any
    actual: Any
    score: float


@dataclass
class DocumentBenchmark:
    sample_id: str
    field_scores: list[FieldScore]
    overall_score: float


def benchmark_sample(sample: dict[str, Any], analyzer: Callable[..., dict[str, Any]] = analyze_document) -> DocumentBenchmark:
    result = analyzer(sample.get("text", ""), sample.get("normalized_subject"))
    expected = sample.get("expected", {})
    actual = {
        "authority": (result.get("authority") or {}).get("value"),
        "subject": (result.get("subject") or {}).get("value"),
        "document_type": (result.get("document_type") or {}).get("value"),
        "short_description": result.get("short_description"),
    }
    scores = [FieldScore(f, expected.get(f), actual.get(f), _score(expected.get(f), actual.get(f))) for f in FIELDS]
    return DocumentBenchmark(sample_id=str(sample.get("sample_id", "unknown")), field_scores=scores, overall_score=round(sum(s.score for s in scores) / len(scores), 4))


def benchmark_file(path: str) -> dict[str, Any]:
    samples = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [benchmark_sample(s) for s in samples]
    field_averages = {f: round(sum(next(x.score for x in r.field_scores if x.field == f) for r in results) / max(1, len(results)), 4) for f in FIELDS}
    overall = round(sum(r.overall_score for r in results) / max(1, len(results)), 4)
    return {"samples": len(results), "overall_score": overall, "field_scores": field_averages, "results": [asdict(r) for r in results]}
