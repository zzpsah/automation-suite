from global_automation.ocr.backend import OCRResult
from global_automation.ocr.region_disagreement import compare_lines


def test_compare_lines_flags_only_disagreeing_lines():
    result = compare_lines([
        OCRResult("पहली पंक्ति\nसरकारी आदेश", "tesseract"),
        OCRResult("पहली पंक्ति\nसरकारी आदे श", "paddleocr"),
    ])
    assert len(result) == 2
    assert result[0].disagreement is False
    assert result[1].disagreement is True
    assert result[1].similarity < 1.0


def test_compare_lines_handles_missing_line_without_crashing():
    result = compare_lines([
        OCRResult("one\ntwo", "a"),
        OCRResult("one", "b"),
    ])
    assert result[-1].texts == ("two", "")


def test_compare_lines_rejects_empty_results():
    try:
        compare_lines([])
    except ValueError:
        pass
    else:
        raise AssertionError("empty results must fail")
