from pathlib import Path

from ocr.benchmark_government import benchmark_file


def test_government_benchmark_scores_known_samples():
    path = Path(__file__).with_name("government_benchmark.jsonl")
    report = benchmark_file(str(path))
    assert report["samples"] == 2
    assert report["field_scores"]["authority"] >= 0.75
    assert report["field_scores"]["subject"] >= 0.75
    assert report["field_scores"]["document_type"] >= 0.75
    assert report["overall_score"] >= 0.70
