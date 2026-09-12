"""Dependency-free OCR regression metrics."""
from __future__ import annotations

def _distance(a: list[str], b: list[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j-1] + (ca != cb)))
        prev = cur
    return prev[-1]

def cer(actual: str, expected: str) -> float:
    if not expected:
        return 0.0 if not actual else 1.0
    return _distance(list(actual), list(expected)) / len(expected)

def wer(actual: str, expected: str) -> float:
    a, b = actual.split(), expected.split()
    if not b:
        return 0.0 if not a else 1.0
    return _distance(a, b) / len(b)

def benchmark(actual: str, expected: str) -> dict[str, float | bool]:
    c, w = cer(actual, expected), wer(actual, expected)
    return {"cer": c, "wer": w, "exact_match": actual.strip() == expected.strip()}
