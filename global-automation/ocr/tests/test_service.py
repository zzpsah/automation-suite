from pathlib import Path

import pytest

from ocr.ocr_service import OCR_SERVICE_VERSION, process_file, process_pdf


def test_service_version_is_present():
    assert OCR_SERVICE_VERSION


def test_missing_pdf_fails_cleanly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        process_pdf(str(tmp_path / "missing.pdf"), str(tmp_path))


def test_non_pdf_is_rejected(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("sample", encoding="utf-8")
    with pytest.raises(ValueError):
        process_file(str(path), str(tmp_path))
