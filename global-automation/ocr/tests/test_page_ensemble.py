from global_automation.ocr.backend import OCRResult
from global_automation.ocr.page_ensemble import ensemble_document, ensemble_page


class FakeBackend:
    def __init__(self, name, text, confidence=None):
        self.name = name
        self.text = text
        self.confidence = confidence

    def extract_image(self, image_path, *, language="hin+eng", psm=6):
        return OCRResult(self.text, self.name, self.confidence)


def test_ensemble_page_preserves_all_backend_outputs():
    result = ensemble_page(
        2,
        "page.jpg",
        [FakeBackend("tesseract", "सरकारी आदेश", .8), FakeBackend("paddleocr", "सरकारी आदेश", .9)],
    )
    assert result.page_number == 2
    assert result.consensus.text == "सरकारी आदेश"
    assert [item.backend for item in result.backend_results] == ["tesseract", "paddleocr"]
    assert result.consensus.disagreement is False


def test_ensemble_document_preserves_page_boundaries():
    pages = ensemble_document(
        [(1, "one.jpg"), (2, "two.jpg")],
        [FakeBackend("tesseract", "page")],
    )
    assert [item.page_number for item in pages] == [1, 2]


def test_ensemble_rejects_invalid_page():
    try:
        ensemble_page(0, "page.jpg", [FakeBackend("tesseract", "page")])
    except ValueError as exc:
        assert "page_number" in str(exc)
    else:
        raise AssertionError("invalid page number must fail")
