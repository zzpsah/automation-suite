from PIL import Image

from ocr.benchmarks.image import image_metrics, metric_delta


def test_image_metrics_are_privacy_safe_and_numeric():
    image = Image.new("L", (100, 80), 200)
    metrics = image_metrics(image)
    assert metrics["width"] == 100
    assert metrics["height"] == 80
    assert metrics["mean_luminance"] == 200
    assert "pixels" not in metrics


def test_metric_delta_is_deterministic():
    before = {"width": 100, "height": 80, "mean_luminance": 100, "contrast": 10, "dark_pixel_ratio": 0.2}
    after = {"width": 200, "height": 160, "mean_luminance": 120, "contrast": 15, "dark_pixel_ratio": 0.1}
    assert metric_delta(before, after) == {
        "width": 100.0,
        "height": 80.0,
        "mean_luminance": 20.0,
        "contrast": 5.0,
        "dark_pixel_ratio": -0.1,
    }
