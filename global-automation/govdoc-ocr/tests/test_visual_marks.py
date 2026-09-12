from pathlib import Path

from PIL import Image, ImageDraw

from visual_marks import analyze_visual_marks


def test_visual_marks_is_evidence_only(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 170, 110), fill=(180, 25, 25))
    draw.line((210, 220, 350, 170), fill=(20, 20, 20), width=5)
    image.save(image_path)

    result = analyze_visual_marks(str(image_path))

    assert result["evidence_only"] is True
    assert "signature" not in result["interpretation"].lower() or "not signature" in result["interpretation"].lower()
    assert result["width"] == 400
    assert result["height"] == 300
    assert isinstance(result["signals"], list)


def test_missing_image_fails_closed(tmp_path: Path):
    missing = tmp_path / "missing.png"
    try:
        analyze_visual_marks(str(missing))
    except FileNotFoundError:
        return
    raise AssertionError("missing visual input must fail closed")
