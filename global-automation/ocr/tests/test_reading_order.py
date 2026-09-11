from ocr.reading_order import ReadingOrderBlock, optimize_reading_order


def block(block_id, page, kind, x, y, width=100, height=20, column=None):
    return ReadingOrderBlock(block_id, page, kind, x, y, width, height, column)


def test_headers_then_columns_then_footer():
    blocks = [
        block("p1-r", 1, "footer", 10, 900),
        block("p1-c2", 1, "body", 600, 120, column=2),
        block("p1-h", 1, "header", 10, 10),
        block("p1-c1b", 1, "body", 50, 300, column=1),
        block("p1-c1a", 1, "body", 50, 120, column=1),
    ]
    assert optimize_reading_order(blocks) == (
        "p1-h", "p1-c1a", "p1-c1b", "p1-c2", "p1-r"
    )


def test_pages_are_ordered_before_next_page():
    blocks = [
        block("p2-body", 2, "body", 10, 10),
        block("p1-body", 1, "body", 10, 10),
    ]
    assert optimize_reading_order(blocks) == ("p1-body", "p2-body")


def test_unassigned_mixed_layout_uses_geometry():
    blocks = [
        block("right-low", 1, "body", 600, 300),
        block("left-low", 1, "body", 50, 300),
        block("right-high", 1, "body", 600, 100),
        block("left-high", 1, "body", 50, 100),
    ]
    assert optimize_reading_order(blocks) == (
        "left-high", "left-low", "right-high", "right-low"
    )


def test_threshold_is_validated():
    try:
        optimize_reading_order([], column_overlap_threshold=1.1)
    except ValueError as exc:
        assert "between 0 and 1" in str(exc)
    else:
        raise AssertionError("invalid threshold should fail")
