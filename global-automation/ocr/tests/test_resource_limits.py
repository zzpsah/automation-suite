from pathlib import Path

import pytest

from ocr.errors import InvalidInputError
from ocr.resource_limits import (
    ConcurrencyLimitError,
    OCRConcurrencyGate,
    ResourceLimitError,
    ResourceLimits,
    check_file_size,
    check_image_pixels,
    check_page_count,
    check_text_size,
    limits_to_dict,
)


def test_file_size_limit(tmp_path: Path):
    path = tmp_path / "doc.bin"
    path.write_bytes(b"12345")
    limits = ResourceLimits(max_file_bytes=5)
    assert check_file_size(path, limits) == 5
    path.write_bytes(b"123456")
    with pytest.raises(ResourceLimitError):
        check_file_size(path, limits)


def test_page_pixel_and_text_limits():
    limits = ResourceLimits(max_pages=2, max_image_pixels=100, max_text_characters=4)
    assert check_page_count(2, limits) == 2
    assert check_image_pixels(10, 10, limits) == 100
    assert check_text_size("abcd", limits) == 4
    with pytest.raises(ResourceLimitError):
        check_page_count(3, limits)
    with pytest.raises(ResourceLimitError):
        check_image_pixels(11, 10, limits)
    with pytest.raises(ResourceLimitError):
        check_text_size("abcde", limits)


def test_concurrency_gate_fails_fast_and_recovers():
    gate = OCRConcurrencyGate(1)
    gate.acquire()
    with pytest.raises(ConcurrencyLimitError):
        gate.acquire()
    gate.release()
    gate.acquire()
    gate.release()


def test_context_manager_releases_slot():
    gate = OCRConcurrencyGate(1)
    with gate:
        with pytest.raises(ConcurrencyLimitError):
            gate.acquire()
    gate.acquire()
    gate.release()


def test_invalid_limits_and_json_shape():
    with pytest.raises(InvalidInputError):
        ResourceLimits(max_pages=0)
    data = limits_to_dict(ResourceLimits(max_concurrent_jobs=3))
    assert data["max_concurrent_jobs"] == 3
    assert all(isinstance(v, int) for v in data.values())
