from pathlib import Path

import pytest
from PIL import Image

from ocr.ocr_service import OCR_SERVICE_VERSION, process_file, process_pdf


def test_service_version_is_present():
    assert OCR_SERVICE_VERSION


def test_missing_pdf_fails_cleanly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        process_pdf(str(tmp_path / "missing.pdf"), str(tmp_path))


def test_non_document_is_rejected(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("sample", encoding="utf-8")
    with pytest.raises(ValueError):
        process_file(str(path), str(tmp_path))


def test_image_is_a_supported_input(tmp_path: Path, monkeypatch):
    source = tmp_path / "sample.png"
    Image.new("RGB", (200, 200), "white").save(source)
    fake = {
        "text": "विषय: परीक्षण",
        "backend": "tesseract",
        "language": "hin+eng",
        "psm": 6,
        "selected_variant": "normalized",
        "selection_score": 0.5,
        "image_quality": {},
        "candidate_count": 4,
    }
    monkeypatch.setattr("ocr.ocr_service.ocr_image_detailed", lambda *args, **kwargs: fake)
    result = process_file(str(source), str(tmp_path))
    assert result["text"] == "विषय: परीक्षण"
    assert result["extraction_method"] == "tesseract-image-quality-aware"
    assert result["ocr"]["backend"] == "tesseract"
