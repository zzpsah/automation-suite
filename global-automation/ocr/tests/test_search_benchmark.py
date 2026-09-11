import pytest

from ocr.benchmarks.search.runner import BenchmarkCase, assert_release_gate, run_benchmark
from ocr.search_index import SearchDocument, DocumentSearchIndex


def test_golden_runner_checks_hit_rate_provenance_and_determinism():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument('doc1', 1, 'b1', 'education authority'))
    cases = (BenchmarkCase('c1', 'education', ('doc1',), 5),)
    report = run_benchmark(cases, lambda q, k: index.search(q, limit=k))
    assert report.passed
    assert report.hit_rate == 1.0
    assert report.provenance_accuracy == 1.0
    assert_release_gate(report)


def test_release_gate_fails_below_threshold():
    index = DocumentSearchIndex()
    cases = (BenchmarkCase('c1', 'missing', ('doc1',), 5),)
    report = run_benchmark(cases, lambda q, k: index.search(q, limit=k))
    with pytest.raises(AssertionError, match='regression gate failed'):
        assert_release_gate(report)
