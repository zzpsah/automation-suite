from dataclasses import replace

from ..backend_benchmark import BackendBenchmark, select_backend


def test_select_backend_prefers_lower_cer() -> None:
    fast = BackendBenchmark("tesseract", 0.12, 0.20, 0.91, 0.1, 100)
    accurate = BackendBenchmark("paddleocr", 0.05, 0.10, 0.80, 0.3, 120)
    assert select_backend([fast, accurate]).backend == "paddleocr"


def test_select_backend_uses_confidence_without_ground_truth() -> None:
    low = BackendBenchmark("tesseract", None, None, 0.72, 0.1, 50)
    high = BackendBenchmark("paddleocr", None, None, 0.94, 0.4, 50)
    assert select_backend([low, high]).backend == "paddleocr"


def test_selection_is_deterministic_on_ties() -> None:
    first = BackendBenchmark("tesseract", None, None, 0.9, 0.2, 50)
    second = BackendBenchmark("paddleocr", None, None, 0.9, 0.2, 50)
    assert select_backend([second, first]).backend == "paddleocr"


def test_empty_results_fail_closed() -> None:
    try:
        select_backend([])
    except ValueError as exc:
        assert "No backend benchmark" in str(exc)
    else:
        raise AssertionError("expected ValueError")
