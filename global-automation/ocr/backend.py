"""Pluggable OCR backend contract for the shared OCR service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OCRResult:
    text: str
    backend: str
    confidence: float | None = None


class OCRBackend(Protocol):
    name: str

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        """Extract text from one rendered image."""


class TesseractBackend:
    """Adapter around the existing Tesseract engine."""

    name = "tesseract"

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        from .ocr_engine import ocr_image

        return OCRResult(text=ocr_image(image_path, lang=language, psm=psm), backend=self.name)


def get_backend(name: str = "tesseract") -> OCRBackend:
    """Resolve a backend by stable name.

    New backends should be registered here only after passing the shared test
    and benchmark suite. No consuming project should import backend internals.
    """
    if name == "tesseract":
        return TesseractBackend()
    raise ValueError(f"Unsupported OCR backend: {name}")
