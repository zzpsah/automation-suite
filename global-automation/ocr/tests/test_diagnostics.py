from ocr.diagnostics import diagnose_page_text, diagnose_pages


def test_blank_page_is_flagged_weak():
    result = diagnose_page_text(1, "\n  \n")
    assert result.blank is True
    assert result.likely_weak is True
    assert result.non_whitespace_characters == 0


def test_normal_page_is_not_weak():
    result = diagnose_page_text(2, "विषय: प्रवेश\nदिनांक: 01/09/2026")
    assert result.page_number == 2
    assert result.blank is False
    assert result.likely_weak is False
    assert result.line_count == 2


def test_page_order_is_deterministic():
    result = diagnose_pages(["पहला पृष्ठ", "दूसरा पृष्ठ"])
    assert [item["page_number"] for item in result] == [1, 2]
    assert all("text" not in item for item in result)
