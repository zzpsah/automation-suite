from ocr.taxonomy import TAXONOMY_VERSION, normalize_category, taxonomy_info


def test_known_category_is_stable():
    assert normalize_category("admission") == "admission"
    assert taxonomy_info("admission") == {
        "version": TAXONOMY_VERSION,
        "key": "admission",
        "label": "Admission / Enrollment",
    }


def test_unknown_category_is_safe_other():
    assert normalize_category("new-unreviewed-category") == "other"
