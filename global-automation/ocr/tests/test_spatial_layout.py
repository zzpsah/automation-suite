from ocr.region_alignment import OCRSpan
from ocr.spatial_layout import classify_layout


def test_classify_layout_preserves_spans_and_regions():
    spans = [
        OCRSpan(text="Header", backend="tesseract", x=100, y=20, width=100, height=20),
        OCRSpan(text="Body", backend="tesseract", x=100, y=500, width=100, height=20),
        OCRSpan(text="Footer", backend="tesseract", x=100, y=950, width=100, height=20),
    ]
    regions = classify_layout(spans, page_width=1000, page_height=1000)
    labels = {region.label for region in regions}
    assert labels == {"header", "body", "footer"}
    assert sum(len(region.spans) for region in regions) == 3


def test_invalid_page_dimensions_fail_closed():
    try:
        classify_layout([], page_width=0, page_height=100)
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid dimensions to fail")
