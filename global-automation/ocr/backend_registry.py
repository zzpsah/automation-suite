"""Stable registry and routing metadata for OCR backends.

Consumers select a capability/profile rather than importing backend classes.
Routing is deterministic and conservative: unsupported capabilities fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from .backend import OCRBackend, get_backend


@dataclass(frozen=True)
class BackendCapabilities:
    """Capabilities advertised by an OCR backend adapter."""

    name: str
    languages: FrozenSet[str]
    layout: bool = False
    confidence: bool = False


_REGISTRY: dict[str, BackendCapabilities] = {
    "tesseract": BackendCapabilities(
        name="tesseract",
        languages=frozenset({"eng", "hin", "hin+eng"}),
        layout=False,
        confidence=False,
    ),
}


def list_backends() -> tuple[BackendCapabilities, ...]:
    """Return registered backend capabilities in stable name order."""
    return tuple(_REGISTRY[name] for name in sorted(_REGISTRY))


def capabilities(name: str) -> BackendCapabilities:
    """Return capabilities for one backend or fail closed."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported OCR backend: {name}") from exc


def resolve_backend(*, language: str = "hin+eng", preferred: str | None = None) -> OCRBackend:
    """Resolve the safest registered backend for a requested language.

    A preferred backend is honored only when it advertises the requested
    language. Otherwise the first compatible backend is selected deterministically.
    """
    candidates = [preferred] if preferred else []
    candidates.extend(name for name in sorted(_REGISTRY) if name not in candidates)
    for name in candidates:
        if name and language in _REGISTRY[name].languages:
            return get_backend(name)
    raise ValueError(f"No OCR backend supports language: {language}")
