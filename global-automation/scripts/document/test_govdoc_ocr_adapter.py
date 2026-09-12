#!/usr/bin/env python3
"""Offline contract tests for the School Pipeline <-> GovDOC OCR adapter."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "global-automation/scripts/document/govdoc_ocr_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("govdoc_ocr_adapter_test", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._CACHE.clear()
    return module


def test_adapter_maps_govdoc_and_preserves_legacy_fields():
    adapter = load_adapter()
    calls = []

    def fake_service(data, filename):
        calls.append((data, filename))
        return {
            "text": "सरकारी विद्यालय सूचना",
            "extraction_method": "GovDOC Vision: Tesseract Hindi+English",
            "subject": "GovDOC subject",
            "authority": "शिक्षा विभाग, बिहार सरकार",
            "short_description": "GovDOC short description",
            "metadata": {
                "subject": {"value": "GovDOC subject"},
                "authority": {"value": "शिक्षा विभाग, बिहार सरकार"},
                "document_type": {"value": "admission", "confidence": "HIGH"},
            },
        }

    adapter.process_pdf_bytes = fake_service

    class Processor:
        @staticmethod
        def embedded_pdf_text(data): return "legacy embedded"
        @staticmethod
        def ocr_pdf(data, workdir): return "legacy ocr"
        @staticmethod
        def extract_metadata(text, filename):
            return ("legacy subject", "legacy authority", "REF-123", "25-06-2026", "2026-06-25", "legacy short", "legacy detail", "other", "Other", "MEDIUM")

    adapter.install(Processor)
    data = b"same-document"
    assert Processor.ocr_pdf(data, "/tmp") == "GovDOC subject"
    result = Processor.extract_metadata("सरकारी विद्यालय सूचना", "notice.pdf")
    assert result[0] == "GovDOC subject"
    assert result[1] == "शिक्षा विभाग, बिहार सरकार"
    assert result[2:5] == ("REF-123", "25-06-2026", "2026-06-25")
    assert result[7:9] == ("admission", "Admission")
    assert result[9] == "HIGH"
    assert len(calls) == 1  # SHA-256 cache prevents duplicate OCR


def test_adapter_routes_jpeg_to_govdoc_image_service():
    adapter = load_adapter()
    calls = []

    def fake_image_service(path, workdir):
        calls.append(path)
        return {
            "text": "image OCR text",
            "extraction_method": "GovDOC Vision: tesseract",
            "metadata": {"document_type": {"value": "other", "confidence": "LOW"}},
            "short_description": "image OCR text",
        }

    adapter.process_image = fake_image_service

    class Processor:
        @staticmethod
        def embedded_pdf_text(data): return ""
        @staticmethod
        def ocr_pdf(data, workdir): return "legacy image ocr"
        @staticmethod
        def extract_metadata(text, filename):
            return ("legacy", "authority", "ref", "date", "normalized", "short", "detail", "other", "Other", "MEDIUM")

    adapter.install(Processor)
    jpeg = b"\xff\xd8\xff\xe0fake-jpeg"
    assert Processor.ocr_pdf(jpeg, "/tmp") == "image OCR text"
    assert len(calls) == 1


def test_adapter_falls_back_when_govdoc_fails():
    adapter = load_adapter()

    def failing_service(data, filename):
        raise RuntimeError("OCR unavailable")

    adapter.process_pdf_bytes = failing_service

    class Processor:
        @staticmethod
        def embedded_pdf_text(data): return "legacy embedded"
        @staticmethod
        def ocr_pdf(data, workdir): return "legacy ocr"
        @staticmethod
        def extract_metadata(text, filename):
            return ("legacy", "authority", "ref", "date", "normalized", "short", "detail", "other", "Other", "MEDIUM")

    adapter.install(Processor)
    assert Processor.embedded_pdf_text(b"x") == "legacy embedded"
    assert Processor.ocr_pdf(b"x", "/tmp") == "legacy ocr"
    assert Processor.extract_metadata("unknown", "x.pdf")[0] == "legacy"
