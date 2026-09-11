from ocr.backend import OCRResult
from ocr.region_alignment import OCRSpan
from ocr.region_consensus import compare_regions


def test_compare_regions_flags_text_disagreement():
    results = [
        OCRResult("राम", "tesseract", spans=(OCRSpan("राम", "tesseract", 10, 10, 40, 15),)),
        OCRResult("रम", "paddleocr", spans=(OCRSpan("रम", "paddleocr", 11, 10, 39, 15),)),
    ]
    rows = compare_regions(results)
    assert len(rows) == 1
    assert rows[0].disagreement is True
    assert rows[0].geometry_score > 0.8


def test_compare_regions_requires_geometry_from_multiple_backends():
    results = [OCRResult("same", "tesseract")]
    assert compare_regions(results) == []
