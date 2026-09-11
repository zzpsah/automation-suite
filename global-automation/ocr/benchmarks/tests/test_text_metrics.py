from __future__ import annotations

from ocr.benchmarks.text_metrics import accuracy_report, cer, normalize_for_eval, wer


def test_unicode_cer_supports_hindi():
    assert cer("विद्यालय", "विद्यालय") == 0.0
    assert cer("विद्यालय", "विधालय") > 0.0


def test_whitespace_normalization_does_not_change_content():
    assert normalize_for_eval("  नमूना\n  दस्तावेज़  ") == "नमूना दस्तावेज़"


def test_wer_counts_word_edits():
    assert wer("one two three", "one two three") == 0.0
    assert wer("one two three", "one four three") == 1 / 3


def test_empty_reference_is_safe():
    assert cer("", "") == 0.0
    assert wer("", "text") == 1.0


def test_accuracy_report_is_json_friendly():
    report = accuracy_report("आदेश जारी", "आदेश जरी")
    assert set(report) == {"cer", "wer", "reference_characters", "reference_words"}
    assert report["reference_words"] == 2
