"""Explicit runtime policy for selecting OCR backends.

The policy is conservative: a caller may request a preferred backend, while
fallback is allowed only among registered backends compatible with language.
Benchmark recommendations are advisory and must be supplied explicitly.
"""
from __future__ import annotations

from .backend import OCRBackend, resolve_backend
from .benchmarks.backend_benchmark import BackendBenchmark, select_backend


def choose_backend(
    *,
    preferred: str = "tesseract",
    language: str = "hin+eng",
    recommendation: BackendBenchmark | None = None,
) -> OCRBackend:
    """Choose a runtime backend without silently trusting stale benchmarks.

    A supplied benchmark recommendation is used only when it is compatible
    with the requested language. Otherwise the normal deterministic registry
    policy applies. The benchmark never changes registry state.
    """
    if recommendation is not None:
        try:
            recommended = resolve_backend(preferred=recommendation.backend, language=language)
        except ValueError:
            recommended = None
        if recommended is not None:
            return recommended
    return resolve_backend(preferred=preferred, language=language)


def choose_from_benchmarks(
    results: list[BackendBenchmark], *, language: str = "hin+eng"
) -> OCRBackend:
    """Return the backend recommended by measured benchmark results."""
    winner = select_backend(results)
    return choose_backend(preferred=winner.backend, language=language)


__all__ = ["choose_backend", "choose_from_benchmarks"]
