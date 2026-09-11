"""Deterministic, privacy-safe metrics for image benchmark cases."""

from __future__ import annotations

from math import hypot
from typing import Any

from PIL import Image


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def image_metrics(image: Image.Image) -> dict[str, Any]:
    """Return lightweight metrics that do not retain image pixels."""
    gray = image.convert("L")
    pixels = list(gray.getdata())
    if not pixels:
        return {
            "width": gray.width,
            "height": gray.height,
            "mean_luminance": 0.0,
            "contrast": 0.0,
            "dark_pixel_ratio": 0.0,
        }

    mean = _mean([float(p) for p in pixels])
    variance = _mean([(float(p) - mean) ** 2 for p in pixels])
    dark_ratio = sum(p < 80 for p in pixels) / len(pixels)
    return {
        "width": gray.width,
        "height": gray.height,
        "mean_luminance": round(mean, 3),
        "contrast": round(hypot(variance, 0.0) ** 0.5, 3),
        "dark_pixel_ratio": round(dark_ratio, 6),
    }


def metric_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, float]:
    """Return numeric before/after deltas for comparable metrics."""
    keys = ("width", "height", "mean_luminance", "contrast", "dark_pixel_ratio")
    return {
        key: round(float(after.get(key, 0.0)) - float(before.get(key, 0.0)), 6)
        for key in keys
    }
