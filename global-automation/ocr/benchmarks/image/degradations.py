"""Controlled document-image degradations for synthetic benchmark generation.

These transformations are deliberately deterministic when a seed is supplied.
They are benchmark fixtures, not production preprocessing.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


@dataclass(frozen=True)
class DegradationSpec:
    rotation: float = 0.0
    contrast: float = 1.0
    brightness: float = 1.0
    noise: float = 0.0
    blur: float = 0.0
    scale: float = 1.0
    perspective: float = 0.0


def apply_degradation(image: Image.Image, spec: DegradationSpec, *, seed: int = 0) -> Image.Image:
    """Apply a reproducible synthetic degradation without mutating the source."""
    if spec.scale <= 0:
        raise ValueError("scale must be > 0")
    if spec.contrast <= 0 or spec.brightness <= 0:
        raise ValueError("contrast and brightness must be > 0")
    if spec.noise < 0 or spec.blur < 0 or spec.perspective < 0:
        raise ValueError("noise, blur and perspective must be >= 0")

    rng = random.Random(seed)
    result = image.convert("RGB").copy()

    if spec.scale != 1.0:
        size = (max(1, round(result.width * spec.scale)), max(1, round(result.height * spec.scale)))
        result = result.resize(size, Image.Resampling.BICUBIC if spec.scale < 1 else Image.Resampling.LANCZOS)

    if spec.rotation:
        result = result.rotate(spec.rotation, expand=True, fillcolor=(255, 255, 255), resample=Image.Resampling.BICUBIC)

    if spec.contrast != 1.0:
        result = ImageEnhance.Contrast(result).enhance(spec.contrast)
    if spec.brightness != 1.0:
        result = ImageEnhance.Brightness(result).enhance(spec.brightness)
    if spec.blur:
        result = result.filter(ImageFilter.GaussianBlur(spec.blur))

    if spec.noise:
        gray = ImageOps.grayscale(result)
        pixels = list(gray.getdata())
        amount = min(1.0, spec.noise)
        changed = []
        for value in pixels:
            if rng.random() < amount:
                value = rng.choice((0, 255))
            changed.append(value)
        noisy = Image.new("L", gray.size)
        noisy.putdata(changed)
        result = noisy.convert("RGB")

    # Perspective is represented conservatively as a small affine shear here.
    # Full projective transforms belong to a future optional vision backend.
    if spec.perspective:
        shear = min(0.25, spec.perspective / 100.0)
        result = result.transform(
            result.size,
            Image.Transform.AFFINE,
            (1.0, shear, -result.height * shear / 2.0, 0.0, 1.0, 0.0),
            resample=Image.Resampling.BICUBIC,
            fillcolor=(255, 255, 255),
        )

    return result
