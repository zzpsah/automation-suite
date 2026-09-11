"""Benchmark OCR backends and select a backend from measured quality signals.

The benchmark is intentionally separate from runtime OCR. It never mutates
runtime configuration or silently promotes a backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable

from .text_metrics import accuracy_report
from ..backend import OCRBackend, OCRResult


@dataclass(frozen=True)
class BackendBenchmark:
    backend: str
    cer: float | None
    wer: float | None
    confidence: float | None
    latency_seconds: float
    characters: int


def benchmark_backend(
    backend: OCRBackend,
    image_path: str,
    *,
    reference_text: str | None = None,
    language: str = "hin+eng",
    psm: int = 6,
    clock: Callable[[], float] = perf_counter,
) -> BackendBenchmark:
    """Run one backend once and return comparable, JSON-friendly metrics."""
    started = clock()
    result: OCRResult = backend.extract_image(image_path, language=language, psm=psm)
    elapsed = max(0.0, clock() - started)
    report = accuracy_report(reference_text, result.text) if reference_text is not None else {}
    return BackendBenchmark(
        backend=result.backend,
        cer=report.get("cer"),
        wer=report.get("wer"),
        confidence=result.confidence,
        latency_seconds=elapsed,
        characters=len(result.text),
    )


def select_backend(results: Iterable[BackendBenchmark]) -> BackendBenchmark:
    """Select the strongest measured result deterministically.

    With ground truth, lower CER/WER wins. Without ground truth, confidence is
    the primary signal and shorter latency is the tie-breaker. This function
    only returns a recommendation; it does not alter registry or runtime state.
    """
    candidates = list(results)
    if not candidates:
        raise ValueError("No backend benchmark results supplied")

    if any(item.cer is not None for item in candidates):
        return min(
            candidates,
            key=lambda item: (
                item.cer if item.cer is not None else float("inf"),
                item.wer if item.wer is not None else float("inf"),
                -(item.confidence if item.confidence is not None else -1.0),
                item.latency_seconds,
                item.backend,
            ),
        )

    return min(
        candidates,
        key=lambda item: (
            -(item.confidence if item.confidence is not None else -1.0),
            item.latency_seconds,
            item.backend,
        ),
    )


__all__ = ["BackendBenchmark", "benchmark_backend", "select_backend"]
