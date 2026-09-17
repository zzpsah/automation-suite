"""Conservative image preprocessing utilities for scanned-document OCR."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

Profile = Literal["none", "document"]


def preprocess_image(image_path: str, output_path: str, *, profile: Profile = "document") -> str:
    """Prepare an image for OCR while preserving the original file.

    Pillow is imported lazily so consumers that only use embedded PDF text do
    not need image-processing imports at module load time.
    """
    if profile == "none":
        return image_path
    if profile != "document":
        raise ValueError(f"Unsupported preprocessing profile: {profile}")

    from PIL import Image, ImageFilter, ImageOps

    source = Path(image_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        gray = ImageOps.grayscale(image)
        # Mild autocontrast and median filtering improve common phone/scanner
        # noise without aggressive thresholding that can destroy Devanagari.
        gray = ImageOps.autocontrast(gray)
        gray = gray.filter(ImageFilter.MedianFilter(size=3))
        gray.save(destination, format="PNG")
    return str(destination)
