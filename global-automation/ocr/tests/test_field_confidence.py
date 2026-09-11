from field_confidence import score_field, score_fields


def test_high_confidence_field_requires_source_evidence():
    result = score_field("issue_date", "2026-09-11", "दिनांक: 2026-09-11")
    assert result.score == 1.0
    assert result.level == "HIGH"
    assert result.evidence is True
    assert result.needs_review is False


def test_missing_evidence_routes_field_to_review():
    result = score_field("reference_number", "ABC/123", "दिनांक: 2026-09-11")
    assert result.score < 0.60
    assert result.needs_review is True


def test_score_fields_returns_only_doubtful_fields_for_review():
    metadata = {
        "subject": "शिक्षक नियुक्ति संबंधी सूचना",
        "authority": "शिक्षा विभाग, बिहार",
        "reference_number": "ABC/123",
        "issue_date": "2026-09-11",
    }
    result = score_fields(
        metadata,
        "विषय: शिक्षक नियुक्ति संबंधी सूचना\nशिक्षा विभाग, बिहार\nदिनांक: 2026-09-11",
    )
    assert result["review"]["required"] is True
    assert result["review"]["fields"] == ["reference_number"]
    assert result["fields"]["subject"]["needs_review"] is False
    assert result["fields"]["authority"]["needs_review"] is False
    assert result["fields"]["issue_date"]["needs_review"] is False


def test_ocr_confidence_is_optional_and_bounded():
    result = score_field(
        "authority",
        "शिक्षा विभाग",
        "शिक्षा विभाग",
        ocr_confidence=2.0,
    )
    assert 0.0 <= result.score <= 1.0
