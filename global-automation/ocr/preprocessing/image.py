"""Document-image normalization and variant generation.

This module deliberately uses Pillow only. It handles common real-world
inputs: phone photos, skewed scans, low contrast, mild noise, EXIF rotation,
and oversized images. Original pixels are never overwritten.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageProfile:
    width: int
    height: int
    mean_luma: float
    contrast: float
    dark_ratio: float
    estimated_skew_degrees: float
    needs_upscale: bool
    needs_deskew: bool


def _gray_pixels(image):
    from PIL import ImageOps
    return ImageOps.grayscale(image)


def _estimate_skew(gray) -> float:
    """Estimate small page skew from dark-pixel covariance."""
    import statistics
    w, h = gray.size
    if w < 80 or h < 80:
        return 0.0
    sample = gray.resize((min(w, 500), min(h, 500)))
    points = []
    for y in range(sample.height):
        for x in range(sample.width):
            if sample.getpixel((x, y)) < 180:
                points.append((x, y))
    if len(points) < 200:
        return 0.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    xx = sum((x - mx) ** 2 for x in xs)
    yy = sum((y - my) ** 2 for y in ys)
    xy = sum((x - mx) * (y - my) for x, y in points)
    if xx == yy:
        return 0.0
    angle = 0.5 * math.degrees(math.atan2(2 * xy, xx - yy))
    if angle > 45:
        angle -= 90
    if angle < -45:
        angle += 90
    return round(max(-8.0, min(8.0, angle)), 2)


def analyze_image(image_path: str) -> dict[str, object]:
    """Return privacy-safe image quality measurements."""
    from PIL import Image, ImageStat
    with Image.open(image_path) as source:
        image = source.copy()
        gray = _gray_pixels(image)
        stat = ImageStat.Stat(gray)
        mean = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        dark = sum(1 for value in gray.resize((100, 100)).getdata() if value < 100) / 10000
        skew = _estimate_skew(gray)
        width, height = image.size
    return asdict(ImageProfile(
        width=width, height=height, mean_luma=round(mean, 2), contrast=round(contrast, 2),
        dark_ratio=round(dark, 4), estimated_skew_degrees=skew,
        needs_upscale=min(width, height) < 1400, needs_deskew=abs(skew) >= 0.7,
    ))


def prepare_variants(image_path: str, output_dir: str, *, strategy: str = "auto", max_dimension: int = 2600, min_dimension: int = 1400) -> list[str]:
    """Create deterministic OCR candidates and return them in preference order."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    if strategy not in {"auto", "quality", "fast"}:
        raise ValueError("strategy must be auto, quality, or fast")
    if max_dimension < min_dimension:
        raise ValueError("max_dimension must be >= min_dimension")
    source = Path(image_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        smallest = min(image.size)
        largest = max(image.size)
        scale = 1.0
        if smallest < min_dimension:
            scale = min_dimension / smallest
        if largest * scale > max_dimension:
            scale = max_dimension / largest
        if abs(scale - 1.0) > 0.01:
            image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
        gray = ImageOps.grayscale(image)
        profile = analyze_image(image_path)
        if profile["needs_deskew"]:
            gray = gray.rotate(-float(profile["estimated_skew_degrees"]), expand=True, fillcolor=255, resample=Image.Resampling.BICUBIC)
        gray = ImageOps.autocontrast(gray, cutoff=1)
        gray = gray.filter(ImageFilter.MedianFilter(size=3))
        sharp = ImageEnhance.Sharpness(gray).enhance(1.25)
        contrast = ImageEnhance.Contrast(sharp).enhance(1.15)
        paths = []
        base = out / "normalized.png"
        gray.save(base, format="PNG", optimize=True)
        paths.append(str(base))
        if strategy != "fast":
            enhanced = out / "enhanced.png"
            contrast.save(enhanced, format="PNG", optimize=True)
            paths.append(str(enhanced))
            threshold = contrast.point(lambda p: 255 if p >= 185 else 0)
            binary = out / "threshold.png"
            threshold.save(binary, format="PNG", optimize=True)
            paths.append(str(binary))
        return paths
