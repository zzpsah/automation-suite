from pathlib import Path

from PIL import Image, ImageDraw

from ocr.preprocessing.image import analyze_image, prepare_variants
from ocr.preprocessing.quality import score_text


def test_image_analysis_is_privacy_safe(tmp_path: Path):
    source = tmp_path / "scan.png"
    Image.new("RGB", (1200, 1800), "white").save(source)
    result = analyze_image(str(source))
    assert result["width"] == 1200
    assert result["height"] == 1800
    assert "text" not in result


def test_prepare_variants_never_overwrites_source(tmp_path: Path):
    source = tmp_path / "scan.png"
    image = Image.new("RGB", (900, 1200), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 100), "Subject: Sarkari Notice", fill="black")
    image.save(source)
    variants = prepare_variants(str(source), str(tmp_path / "work"))
    assert len(variants) == 3
    assert source.exists()
    assert all(Path(path).exists() for path in variants)


def test_quality_score_orders_empty_below_usable_text():
    assert score_text("") == 0.0
    assert score_text("विषय: महत्वपूर्ण सरकारी सूचना\nदिनांक: 01/09/2026") > 0.3
