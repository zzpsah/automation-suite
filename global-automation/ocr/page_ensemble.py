"""Page-level ensemble and disagreement diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .backend import OCRBackend, OCRResult
from .fusion import ConsensusResult, consensus


@dataclass(frozen=True)
class PageEnsembleResult:
    page_number: int
    consensus: ConsensusResult
    backend_results: tuple[OCRResult, ...]


def ensemble_page(
    page_number: int,
    image_path: str,
    backends: Iterable[OCRBackend],
    *,
    language: str = "hin+eng",
    psm: int = 6,
) -> PageEnsembleResult:
    """Run supplied backends on one page and preserve all outputs."""
    if page_number < 1:
        raise ValueError("page_number must be >= 1")
    results: list[OCRResult] = []
    for backend in backends:
        results.append(backend.extract_image(image_path, language=language, psm=psm))
    if not results:
        raise ValueError("No OCR backends supplied")
    return PageEnsembleResult(
        page_number=page_number,
        consensus=consensus(results),
        backend_results=tuple(results),
    )


def ensemble_document(
    pages: Iterable[tuple[int, str]],
    backends: Iterable[OCRBackend],
    *,
    language: str = "hin+eng",
    psm: int = 6,
) -> tuple[PageEnsembleResult, ...]:
    """Run an ensemble page-by-page without losing page boundaries."""
    backend_list = tuple(backends)
    if not backend_list:
        raise ValueError("No OCR backends supplied")
    return tuple(
        ensemble_page(page_number, image_path, backend_list, language=language, psm=psm)
        for page_number, image_path in pages
    )


__all__ = ["PageEnsembleResult", "ensemble_page", "ensemble_document"]
