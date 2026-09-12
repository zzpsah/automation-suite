from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
ADAPTER_PATH = ROOT / "global-automation" / "scripts" / "document" / "govdoc_ocr_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("govdoc_ocr_adapter_test", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provenance_contract_is_compact_and_explicit():
    adapter = load_adapter()
    result = {
        "ocr_service_version": "4.3",
        "extraction_method": "GovDOC Vision: tesseract Hindi+English",
        "ocr": {"backend": "tesseract", "language": "hin+eng"},
        "pages": [{"page_number": 1}, {"page_number": 2}],
    }
    assert adapter._provenance(result) == {
        "service": "GovDOC Vision",
        "service_version": "4.3",
        "extraction_method": "GovDOC Vision: tesseract Hindi+English",
        "backend": "tesseract",
        "language": "hin+eng",
        "page_count": 2,
    }


def test_install_overrides_document_method_without_changing_storage_contract():
    adapter = load_adapter()
    captured = {}

    def embedded(data):
        return ""

    def ocr(data, workdir):
        return "ocr"

    def metadata(text, filename):
        return ("subject", "authority", "ref", "01.01.2026", "2026-01-01", "short", "summary", "other", "Other", "MEDIUM")

    def insert(table, payload):
        captured["table"] = table
        captured["payload"] = payload
        return {"id": "doc-1"}

    def patch(table, rid, payload):
        captured["patch"] = (table, rid, payload)

    def process(row):
        return True

    processor = SimpleNamespace(
        embedded_pdf_text=embedded,
        ocr_pdf=ocr,
        extract_metadata=metadata,
        db_insert=insert,
        db_patch=patch,
        process=process,
    )

    adapter.install(processor)
    adapter._LAST_RESULT = {
        "ocr_service_version": "4.3",
        "extraction_method": "GovDOC Vision: tesseract Hindi+English",
        "ocr": {"backend": "tesseract", "language": "hin+eng"},
        "pages": [{"page_number": 1}],
    }

    processor.db_insert("documents", {"extraction_method": "legacy"})
    assert captured["payload"]["extraction_method"] == "GovDOC Vision: tesseract Hindi+English"

    processor.db_patch("telegram_intake", "intake-1", {"status": "Processed", "metadata": {}})
    assert captured["patch"][2]["metadata"]["govdoc_ocr"]["service"] == "GovDOC Vision"
    assert captured["patch"][2]["metadata"]["govdoc_ocr"]["service_version"] == "4.3"

    # The adapter only changes OCR provenance; the original processor still owns
    # the database operation itself.
    assert captured["table"] == "documents"
