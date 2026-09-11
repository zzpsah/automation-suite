"""Pluggable OCR backend contract and deterministic backend registry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .region_alignment import OCRSpan


@dataclass(frozen=True)
class OCRResult:
    text: str
    backend: str
    # Backends that expose confidence MUST normalize it to [0, 1].
    confidence: float | None = None
    # Optional geometry-aware spans; text-only consumers remain compatible.
    spans: tuple[OCRSpan, ...] = ()


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

        text = ocr_image(image_path, lang=language, psm=psm)
        spans: list[OCRSpan] = []
        try:
            import pytesseract
            from pytesseract import Output
            data = pytesseract.image_to_data(image_path, lang=language, config=f"--psm {psm}", output_type=Output.DICT)
            for i, raw in enumerate(data.get("text", [])):
                value = str(raw).strip()
                if not value:
                    continue
                try:
                    conf = float(data["conf"][i]) / 100.0
                except (KeyError, TypeError, ValueError):
                    conf = None
                spans.append(OCRSpan(
                    text=value,
                    backend=self.name,
                    x=float(data["left"][i]),
                    y=float(data["top"][i]),
                    width=float(data["width"][i]),
                    height=float(data["height"][i]),
                    confidence=max(0.0, min(1.0, conf)) if conf is not None and conf >= 0 else None,
                ))
        except (ImportError, RuntimeError, OSError):
            spans = []
        return OCRResult(text=text, backend=self.name, spans=tuple(spans))


# Factories are used so optional backends are imported only when selected.
_BACKENDS: dict[str, type[OCRBackend]] = {"tesseract": TesseractBackend}


def register_backend(name: str, backend: type[OCRBackend], *, replace: bool = False) -> None:
    """Register a backend explicitly; accidental replacement is rejected."""
    if not name or not getattr(backend, "name", None):
        raise ValueError("Backend name and backend.name are required")
    if name != backend.name:
        raise ValueError("Registry name must match backend.name")
    if name in _BACKENDS and not replace:
        raise ValueError(f"OCR backend already registered: {name}")
    _BACKENDS[name] = backend


def register_optional_backends() -> None:
    """Register built-in optional adapters without importing their dependencies."""
    from .backends.paddleocr import PaddleOCRBackend

    register_backend(PaddleOCRBackend.name, PaddleOCRBackend)


def list_backends() -> tuple[str, ...]:
    """Return registered backend names in deterministic order."""
    return tuple(sorted(_BACKENDS))


def _language_supported(backend: OCRBackend, language: str) -> bool:
    requested = {part.strip() for part in language.split("+") if part.strip()}
    return bool(requested) and requested.issubset(backend.supported_languages)


def get_backend(name: str = "tesseract", *, language: str | None = None) -> OCRBackend:
    """Resolve a backend and optionally validate requested language support."""
    try:
        backend = _BACKENDS[name]()
    except KeyError as exc:
        raise ValueError(f"Unsupported OCR backend: {name}") from exc
    if language is not None and not _language_supported(backend, language):
        raise ValueError(f"Backend {name!r} does not support language {language!r}")
    return backend


def resolve_backend(*, preferred: str = "tesseract", language: str = "hin+eng") -> OCRBackend:
    """Choose a compatible backend deterministically, failing closed if none exist."""
    if preferred in _BACKENDS:
        backend = get_backend(preferred)
        if _language_supported(backend, language):
            return backend
    for name in list_backends():
        backend = get_backend(name)
        if _language_supported(backend, language):
            return backend
    raise ValueError(f"No OCR backend supports language {language!r}")


__all__ = [
    "OCRResult",
    "OCRBackend",
    "TesseractBackend",
    "register_backend",
    "register_optional_backends",
    "list_backends",
    "get_backend",
    "resolve_backend",
]
