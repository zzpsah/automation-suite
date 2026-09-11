"""Conservative image preprocessing for scanned/photographed documents."""
from __future__ import annotations
from pathlib import Path

def preprocess_image(image_path: str, output_path: str, *, profile: str = "document") -> dict:
    if profile == "none": return {"path": image_path, "transformations": []}
    if profile != "document": raise ValueError(f"Unsupported preprocessing profile: {profile}")
    from PIL import Image, ImageFilter, ImageOps
    source, dest = Path(image_path), Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        original_size = image.size
        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray)
        gray = gray.filter(ImageFilter.MedianFilter(size=3))
        gray.save(dest, format="PNG")
    return {"path": str(dest), "original_size": list(original_size), "output_size": list(gray.size), "transformations": ["grayscale", "autocontrast", "median_filter"]}
