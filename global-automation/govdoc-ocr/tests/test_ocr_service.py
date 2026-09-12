from govdoc_ocr.ocr_service import OCR_SERVICE_VERSION, _clean, process_pdf


def test_version_is_present():
    assert OCR_SERVICE_VERSION == "3.1"


def test_clean_removes_control_and_excess_whitespace():
    assert _clean("  hello\tworld\n\n\nnext  ") == "hello world\n\nnext"


def test_mixed_pdf_routes_each_page_independently(tmp_path, monkeypatch):
    pdf = tmp_path / "mixed.pdf"
    pdf.write_bytes(b"placeholder")

    monkeypatch.setattr(
        "govdoc_ocr.ocr_service._embedded_pages",
        lambda path: ["Embedded page text", ""],
    )

    def fake_render_page(path, workdir, page_number):
        return tmp_path / f"rendered-{page_number}.jpg"

    def fake_ocr_page(image, workdir, page_number, backend_name="tesseract", language="hin+eng"):
        text = "OCR page text"
        return text, {
            "page_number": page_number,
            "text": text,
            "backend": backend_name,
            "confidence": None,
            "preprocessing": None,
            "extraction_method": f"ocr:{backend_name}",
        }

    monkeypatch.setattr("govdoc_ocr.ocr_service._render_page", fake_render_page)
    monkeypatch.setattr("govdoc_ocr.ocr_service._ocr_page", fake_ocr_page)

    result = process_pdf(str(pdf), str(tmp_path), min_embedded_chars=5)

    assert result["ocr_service_version"] == "3.1"
    assert result["extraction_method"] == "GovDOC Vision: mixed embedded-text/tesseract OCR"
    assert result["pages"][0]["extraction_method"] == "embedded-text"
    assert result["pages"][1]["extraction_method"] == "ocr:tesseract"
    assert result["pages"][1]["page_number"] == 2
    assert result["text"] == "Embedded page text\n\nOCR page text"


def test_all_embedded_pdf_does_not_start_ocr(tmp_path, monkeypatch):
    pdf = tmp_path / "text.pdf"
    pdf.write_bytes(b"placeholder")
    monkeypatch.setattr(
        "govdoc_ocr.ocr_service._embedded_pages",
        lambda path: ["This page has enough embedded text"],
    )

    def fail_render(*args, **kwargs):
        raise AssertionError("OCR rendering should not run for usable embedded text")

    monkeypatch.setattr("govdoc_ocr.ocr_service._render_page", fail_render)
    result = process_pdf(str(pdf), str(tmp_path), min_embedded_chars=5)

    assert result["extraction_method"] == "GovDOC Vision: embedded-text"
    assert result["pages"][0]["extraction_method"] == "embedded-text"
