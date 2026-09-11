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
    supported_languages: frozenset[str]

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        """Extract text from one rendered image."""


class TesseractBackend:
    """Adapter around the existing Tesseract engine."""

    name = "tesseract"
    supported_languages = frozenset({"eng", "hin", "hin+eng"})

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        from .ocr_engine import ocr_image

        return OCRResult(text=ocr_image(image_path, lang=language, psm=psm), backend=self.name)


_BACKENDS: dict[str, type[OCRBackend]] = {"tesseract": TesseractBackend}


def list_backends() -> tuple[str, ...]:
    """Return registered backend names in deterministic order."""
    return tuple(sorted(_BACKENDS))


def _language_supported(backend: OCRBackend, language: str) -> bool:
    requested = {part.strip() for part in language.split("+") if part.strip()}
    return bool(requested) and requested.issubset(backend.supported_languages)


def get_backend(name: str = "tesseract", *, language: str | None = None) -> OCRBackend:
    """Resolve a backend and optionally validate requested language support.

    Backend names are explicit and deterministic. Unsupported names or language
    combinations fail closed rather than silently selecting another engine.
    """
    try:
        backend = _BACKENDS[name]()
    except KeyError as exc:
        raise ValueError(f"Unsupported OCR backend: {name}") from exc
    if language is not None and not _language_supported(backend, language):
        raise ValueError(f"Backend {name!r} does not support language {language!r}")
    return backend


def resolve_backend(*, preferred: str = "tesseract", language: str = "hin+eng") -> OCRBackend:
    """Choose a compatible registered backend deterministically.

    The preferred backend wins when compatible. Otherwise the first compatible
    registered backend is selected. If none are compatible, fail closed.
    """
    if preferred in _BACKENDS:
        backend = get_backend(preferred)
        if _language_supported(backend, language):
            return backend
    for name in list_backends():
        backend = get_backend(name)
        if _language_supported(backend, language):
            return backend
    raise ValueError(f"No OCR backend supports language {language!r}")
