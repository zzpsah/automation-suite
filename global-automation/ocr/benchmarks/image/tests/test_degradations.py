from PIL import Image, ImageChops

from ocr.benchmarks.image.degradations import DegradationSpec, apply_degradation


def test_degradation_is_deterministic():
    image = Image.new("RGB", (120, 80), "white")
    spec = DegradationSpec(rotation=2.0, contrast=0.7, noise=0.08, blur=0.4, scale=0.8)
    first = apply_degradation(image, spec, seed=42)
    second = apply_degradation(image, spec, seed=42)
    assert ImageChops.difference(first, second).getbbox() is None


def test_degradation_does_not_mutate_source():
    image = Image.new("RGB", (120, 80), "white")
    original = image.copy()
    apply_degradation(image, DegradationSpec(rotation=3), seed=1)
    assert ImageChops.difference(image, original).getbbox() is None
