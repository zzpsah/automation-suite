from ocr.multipage_intelligence import analyze_pages


def test_repeated_header_footer_detection():
    result = analyze_pages([
        "Department of Education\nPage one\nFooter",
        "Department of Education\nPage two\nFooter",
        "Department of Education\nPage three\nFooter",
    ])
    assert result["page_count"] == 3
    assert "department of education" in result["repeated_headers"]
    assert "footer" in result["repeated_footers"]
    assert all(p["repeated_header"] for p in result["pages"])


def test_invalid_threshold_fails_closed():
    try:
        analyze_pages(["a"], repeated_threshold=0)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid threshold must raise")
