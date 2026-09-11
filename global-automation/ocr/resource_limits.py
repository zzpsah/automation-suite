"""P32 safety limits for OCR workloads.

The module is intentionally dependency-free and side-effect-free. It provides
admission checks before expensive OCR work starts and a small concurrency gate
for callers that want to protect CPU/RAM on shared workers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

from .errors import InvalidInputError, OCRPlatformError


class ResourceLimitError(OCRPlatformError):
    """Raised when an OCR workload exceeds a configured safety limit."""

    code = "RESOURCE_LIMIT_EXCEEDED"


class ConcurrencyLimitError(ResourceLimitError):
    """Raised when no OCR worker slot is immediately available."""

    code = "CONCURRENCY_LIMIT_EXCEEDED"


@dataclass(frozen=True)
class ResourceLimits:
    """Hard admission limits for one document request."""

    max_file_bytes: int = 50 * 1024 * 1024
    max_pages: int = 100
    max_image_pixels: int = 40_000_000
    max_text_characters: int = 2_000_000
    max_concurrent_jobs: int = 2

    def __post_init__(self) -> None:
        if self.max_file_bytes <= 0 or self.max_pages <= 0 or self.max_image_pixels <= 0:
            raise InvalidInputError("resource limits must be positive")
        if self.max_text_characters <= 0 or self.max_concurrent_jobs <= 0:
            raise InvalidInputError("resource limits must be positive")


def check_file_size(path: str | Path, limits: ResourceLimits) -> int:
    """Reject files larger than the configured byte limit."""
    size = Path(path).stat().st_size
    if size > limits.max_file_bytes:
        raise ResourceLimitError(
            f"file size {size} exceeds limit {limits.max_file_bytes} bytes"
        )
    return size


def check_page_count(page_count: int, limits: ResourceLimits) -> int:
    """Reject documents containing too many pages."""
    if page_count < 0:
        raise InvalidInputError("page_count cannot be negative")
    if page_count > limits.max_pages:
        raise ResourceLimitError(
            f"page count {page_count} exceeds limit {limits.max_pages}"
        )
    return page_count


def check_image_pixels(width: int, height: int, limits: ResourceLimits) -> int:
    """Reject images whose pixel count is too large for safe processing."""
    if width <= 0 or height <= 0:
        raise InvalidInputError("image dimensions must be positive")
    pixels = width * height
    if pixels > limits.max_image_pixels:
        raise ResourceLimitError(
            f"image pixels {pixels} exceed limit {limits.max_image_pixels}"
        )
    return pixels


def check_text_size(text: str, limits: ResourceLimits) -> int:
    """Reject unexpectedly huge OCR/derived text payloads."""
    size = len(text)
    if size > limits.max_text_characters:
        raise ResourceLimitError(
            f"text characters {size} exceed limit {limits.max_text_characters}"
        )
    return size


class OCRConcurrencyGate:
    """Non-blocking worker gate; callers fail fast instead of queueing forever."""

    def __init__(self, max_concurrent_jobs: int = 2) -> None:
        if max_concurrent_jobs <= 0:
            raise InvalidInputError("max_concurrent_jobs must be positive")
        self._semaphore = BoundedSemaphore(max_concurrent_jobs)

    def acquire(self) -> None:
        if not self._semaphore.acquire(blocking=False):
            raise ConcurrencyLimitError("maximum concurrent OCR jobs reached")

    def release(self) -> None:
        self._semaphore.release()

    def __enter__(self) -> "OCRConcurrencyGate":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.release()


def limits_to_dict(limits: ResourceLimits) -> dict[str, int]:
    return {
        "max_file_bytes": limits.max_file_bytes,
        "max_pages": limits.max_pages,
        "max_image_pixels": limits.max_image_pixels,
        "max_text_characters": limits.max_text_characters,
        "max_concurrent_jobs": limits.max_concurrent_jobs,
    }
