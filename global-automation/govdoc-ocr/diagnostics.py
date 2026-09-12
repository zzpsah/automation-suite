"""Privacy-safe diagnostics for document image preprocessing."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ImageDiagnostics:
    width: int | None
    height: int | None
    format: str | None
    file_size_bytes: int | None
    grayscale: bool | None
    quality_score: float | None
    blur_score: float | None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"notes": list(self.notes)}

def inspect_image(path: str) -> ImageDiagnostics:
    p = Path(path)
    size = p.stat().st_size if p.exists() else None
    try:
        from PIL import Image, ImageStat, ImageFilter
        with Image.open(p) as image:
            gray = image.convert("L")
            variance = ImageStat.Stat(gray).var[0]
            # A conservative, deterministic proxy; it is not an OCR confidence.
            quality = max(0.0, min(1.0, variance / 2500.0))
            blur = max(0.0, min(1.0, variance / 5000.0))
            return ImageDiagnostics(image.width, image.height, image.format, size,
                                    image.mode == "L", quality, blur)
    except Exception as exc:
        return ImageDiagnostics(None, None, None, size, None, None, None,
                                (f"diagnostics-unavailable:{type(exc).__name__}",))
