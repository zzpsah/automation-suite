from ocr.training.candidate_policy import validate_candidate


def test_repeated_spelling_variant_can_be_candidate():
    assert validate_candidate("विधालय", "विद्यालय", frequency=3) == (True, "candidate")


def test_single_observation_is_not_promoted():
    assert validate_candidate("विधालय", "विद्यालय", frequency=1)[0] is False


def test_dates_are_never_language_candidates():
    assert validate_candidate("12/06/2026", "13/06/2026", frequency=10)[0] is False
