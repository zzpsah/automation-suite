from handwriting_review import candidates_from_regions, review_contract


def test_low_confidence_region_becomes_review_candidate():
    regions = [{"id": "r1", "bbox": [1, 2, 30, 40], "confidence": 0.4}]
    candidates = candidates_from_regions(regions)
    assert len(candidates) == 1
    assert candidates[0].region_id == "r1"
    assert candidates[0].bbox == [1, 2, 30, 40]


def test_review_contract_does_not_claim_recognition():
    result = review_contract([{"id": "r1", "bbox": [1, 2, 3, 4], "confidence": 0.5}])
    assert result["supported"] is True
    assert result["recognition_available"] is False
    assert result["evidence_only"] is True
    assert result["candidate_count"] == 1
