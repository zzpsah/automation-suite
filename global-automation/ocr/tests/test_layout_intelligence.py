from ocr.layout_intelligence import analyze_layout, detect_columns, detect_table
from ocr.region_alignment import OCRSpan
from ocr.text_reconstruction import group_lines


def span(text, x, y, width=40, height=10):
    return OCRSpan(text, "test", x, y, width, height)


def test_group_lines_and_columns():
    lines = group_lines([
        span("A", 10, 10), span("B", 100, 10),
        span("C", 10, 30), span("D", 100, 30),
    ])
    columns = detect_columns(lines)
    assert len(lines) == 2
    assert len(columns) == 2


def test_table_detection_requires_stable_columns():
    lines = group_lines([
        span("1", 10, 10), span("Ram", 100, 10),
        span("2", 10, 30), span("Shyam", 100, 30),
    ])
    cells = detect_table(lines)
    assert [(c.row, c.column, c.text) for c in cells] == [
        (1, 1, "1"), (1, 2, "Ram"),
        (2, 1, "2"), (2, 2, "Shyam"),
    ]


def test_layout_analysis_is_json_friendly():
    result = analyze_layout([span("विषय", 10, 10), span("पत्र", 10, 40)], page_height=100)
    assert result["span_count"] == 2
    assert result["line_count"] == 2
    assert result["blocks"][0]["type"] == "header"
