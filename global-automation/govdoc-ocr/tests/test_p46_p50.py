from govdoc_ocr.reading_order import line_text, reading_lines, reading_order
from govdoc_ocr.layout import table_candidates


def test_p46_geometry_is_kept_in_deterministic_reading_order():
    regions = [
        {"id": "r3", "bbox": [100, 80, 160, 100], "text": "दूसरा"},
        {"id": "r1", "bbox": [10, 20, 60, 40], "text": "पहला"},
        {"id": "r2", "bbox": [70, 20, 120, 40], "text": "भाग"},
    ]
    assert [r["id"] for r in reading_order(regions)] == ["r1", "r2", "r3"]
    assert line_text(regions) == ["पहला भाग", "दूसरा"]


def test_p47_lines_are_evidence_not_text_correction():
    regions = [
        {"id": "a", "bbox": [0, 0, 30, 20], "text": "मूल"},
        {"id": "b", "bbox": [35, 4, 70, 24], "text": "पाठ"},
    ]
    lines = reading_lines(regions, y_tolerance=6)
    assert len(lines) == 1
    assert [r["text"] for r in lines[0]] == ["मूल", "पाठ"]


def test_p48_table_candidates_remain_evidence_only():
    regions = [
        {"id": "1", "bbox": [0, 0, 50, 20], "text": "क्रम"},
        {"id": "2", "bbox": [70, 0, 130, 20], "text": "नाम"},
        {"id": "3", "bbox": [0, 40, 50, 60], "text": "1"},
    ]
    candidates = table_candidates(regions)
    assert len(candidates) == 1
    assert [r["text"] for r in candidates[0]] == ["क्रम", "नाम"]


def test_p49_empty_geometry_stays_empty():
    assert reading_order([]) == []
    assert line_text([]) == []


def test_p50_does_not_invent_missing_text():
    regions = [{"id": "r1", "bbox": [0, 0, 20, 20], "text": ""}]
    assert line_text(regions) == [""]
