"""Small benchmark harness for comparing OCR backends on the same corpus.

It intentionally records timing and extraction output metadata only; document
content should not be uploaded or logged by this utility.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .backend import get_backend


@dataclass
class BenchmarkResult:
    backend: str
    elapsed_seconds: float
    output_characters: int


def benchmark_images(image_paths: list[str], backend_name: str = "tesseract", *, language: str = "hin+eng", psm: int = 6) -> dict[str, Any]:
    backend = get_backend(backend_name)
    started = time.perf_counter()
    chars = 0
    for path in image_paths:
        result = backend.extract_image(path, language=language, psm=psm)
        chars += len(result.text)
    elapsed = time.perf_counter() - started
    result = BenchmarkResult(backend=backend.name, elapsed_seconds=round(elapsed, 4), output_characters=chars)
    return asdict(result)


def collect_images(directory: str) -> list[str]:
    """Collect common rendered image files deterministically."""
    root = Path(directory)
    return [str(p) for p in sorted(root.glob("**/*")) if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}]
