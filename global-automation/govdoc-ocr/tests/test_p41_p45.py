from govdoc_ocr.handwriting import handwriting_status, review_flags
from govdoc_ocr.layout import table_candidates
from govdoc_ocr.backend_policy import choose_backend


def test_p41_backend_escalation_is_explainable():
    d=choose_backend(available=("tesseract","paddleocr"),quality_score=.2)
    assert d.backend=="paddleocr" and d.escalated is True
    assert "low image quality" in d.reason


def test_p42_table_detection_is_evidence_only():
    regions=[{"id":"1","bbox":[0,0,50,20],"text":"A"},{"id":"2","bbox":[60,0,110,20],"text":"B"}]
    assert len(table_candidates(regions))==1


def test_p43_handwriting_never_claims_recognition():
    status=handwriting_status(backend="tesseract",regions=[])
    assert status["supported"] is False
    assert status["recognized"] is False


def test_p44_low_confidence_creates_review_flag():
    flags=review_flags([{"id":"r1","confidence":.4}])
    assert flags[0]["requires_review"] is True


def test_p45_review_flag_is_not_auto_correction():
    status=handwriting_status(backend="tesseract",regions=[{"id":"r1","confidence":.4}])
    assert status["requires_review"] is True
    assert status["recognized"] is False
