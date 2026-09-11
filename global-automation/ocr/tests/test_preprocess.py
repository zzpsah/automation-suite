from pathlib import Path

from PIL import Image

from ocr.preprocess import preprocess_image


def test_document_profile_preserves_original(tmp_path: Path):
    source = tmp_path / "source.png"
    output = tmp_path / "work" / "processed.png"
    Image.new("L", (100, 100), 180).save(source)
    result = preprocess_image(str(source), str(output), profile="document")
    assert result == str(output)
    assert source.exists()
    assert output.exists()


def test_none_profile_does_not_copy(tmp_path: Path):
    source = tmp_path / "source.png"
    Image.new("L", (10, 10), 255).save(source)
    assert preprocess_image(str(source), str(tmp_path / "unused.png"), profile="none") == str(source)
