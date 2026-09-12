"""Evidence-only visual mark triage for scanned government documents.

This module does not identify, authenticate, or interpret a signature/stamp. It
only reports deterministic visual evidence that can help a downstream review
workflow decide whether a page deserves closer inspection.
"""
from __future__ import annotations

from pathlib import Path


def _pixel_metrics(image_path: str, max_side: int = 700):
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    original_size = image.size
    image.thumbnail((max_side, max_side))
    pixels = list(image.getdata())
    if not pixels:
        return original_size, 0.0, 0.0, 0.0

    dark = 0
    chromatic = 0
    transitions = 0
    total = len(pixels)
    previous = None
    for r, g, b in pixels:
        if max(r, g, b) < 105:
            dark += 1
        if max(r, g, b) - min(r, g, b) > 42:
            chromatic += 1
        if previous is not None:
            if abs(r - previous[0]) + abs(g - previous[1]) + abs(b - previous[2]) > 120:
                transitions += 1
        previous = (r, g, b)

    return original_size, dark / total, chromatic / total, transitions / max(1, total - 1)


def analyze_visual_marks(image_path: str) -> dict:
    """Return conservative visual-mark evidence for one raster page.

    The output intentionally uses ``evidence`` and ``review_hint`` language;
    it must never be treated as proof of a signature, stamp, seal, or validity.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(image_path)

    size, dark_ratio, chromatic_ratio, transition_ratio = _pixel_metrics(str(path))

    # Broad heuristics are deliberately low-risk. They flag pages for review,
    # rather than asserting that a particular object exists.
    signals = []
    if dark_ratio >= 0.055:
        signals.append("dark-ink-evidence")
    if chromatic_ratio >= 0.012:
        signals.append("colored-ink-evidence")
    if transition_ratio >= 0.035:
        signals.append("high-local-contrast-evidence")

    review_hint = "review-visual-marks" if len(signals) >= 2 else "no-strong-visual-mark-signal"
    return {
        "width": size[0],
        "height": size[1],
        "signals": signals,
        "dark_ink_ratio": round(dark_ratio, 5),
        "chromatic_ink_ratio": round(chromatic_ratio, 5),
        "local_contrast_ratio": round(transition_ratio, 5),
        "review_hint": review_hint,
        "evidence_only": True,
        "interpretation": "Visual evidence only; not signature/stamp detection or authenticity verification.",
    }
