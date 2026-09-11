from ocr.region_alignment import OCRSpan, align_regions


def test_align_regions_matches_overlapping_boxes():
    spans = [
        OCRSpan("पत्रांक", "tesseract", 10, 10, 80, 20),
        OCRSpan("पत्रांक", "paddleocr", 12, 11, 78, 20),
    ]
    pairs = align_regions(spans)
    assert len(pairs) == 1
    assert pairs[0][0].backend != pairs[0][1].backend
    assert pairs[0][2] > 0.8


def test_align_regions_keeps_unrelated_regions_unmatched():
    spans = [
        OCRSpan("ऊपर", "tesseract", 0, 0, 40, 10),
        OCRSpan("नीचे", "paddleocr", 500, 500, 40, 10),
    ]
    assert align_regions(spans) == []


def test_alignment_is_deterministic():
    spans = [
        OCRSpan("A", "paddleocr", 20, 20, 30, 10),
        OCRSpan("A", "tesseract", 21, 20, 30, 10),
    ]
    assert align_regions(spans) == align_regions(list(reversed(spans)))
