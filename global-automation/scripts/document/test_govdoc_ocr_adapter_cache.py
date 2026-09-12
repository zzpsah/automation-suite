"""Offline tests for adapter cache isolation and idempotent OCR calls."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "global-automation/scripts/document/govdoc_ocr_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("govdoc_ocr_adapter_cache_test", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._CACHE.clear()
    return module


def test_cache_key_isolated_by_document_filename():
    adapter = load_adapter()
    calls = []

    def fake_service(data, filename):
        calls.append((data, filename))
        return {"text": f"ocr:{filename}", "extraction_method": "GovDOC Vision: tesseract", "metadata": {}}

    adapter.process_pdf_bytes = fake_service

    class Processor:
        @staticmethod
        def embedded_pdf_text(data):
            return "legacy"

        @staticmethod
        def ocr_pdf(data, workdir):
            return "legacy"

        @staticmethod
        def extract_metadata(text, filename):
            return ("legacy", "authority", "ref", "date", "normalized", "short", "detail", "other", "Other", "MEDIUM")

    adapter.install(Processor)
    assert Processor.ocr_pdf(b"same", "/tmp") == "ocr:document.pdf"
    assert Processor.ocr_pdf(b"same", "/tmp") == "ocr:document.pdf"
    assert len(calls) == 1


def test_different_payloads_are_not_deduplicated():
    adapter = load_adapter()
    calls = []

    def fake_service(data, filename):
        calls.append(data)
        return {"text": data.decode(), "extraction_method": "GovDOC Vision: tesseract", "metadata": {}}

    adapter.process_pdf_bytes = fake_service

    class Processor:
        @staticmethod
        def embedded_pdf_text(data): return ""
        @staticmethod
        def ocr_pdf(data, workdir): return "legacy"
        @staticmethod
        def extract_metadata(text, filename):
            return ("legacy", "authority", "ref", "date", "normalized", "short", "detail", "other", "Other", "MEDIUM")

    adapter.install(Processor)
    assert Processor.ocr_pdf(b"one", "/tmp") == "one"
    assert Processor.ocr_pdf(b"two", "/tmp") == "two"
    assert calls == [b"one", b"two"]
