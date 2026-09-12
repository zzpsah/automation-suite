"""Bridge the production document processor to the shared GovDOC Vision engine.

GovDOC owns OCR and government-document intelligence. The existing School
Document Pipeline remains responsible for storage, lifecycle and publication.
Legacy extraction is retained for fields GovDOC does not currently expose.
"""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path
from typing import Any


def _service():
    root = Path(__file__).resolve().parents[2] / "govdoc-ocr"
    init = root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "govdoc_ocr", init, submodule_search_locations=[str(root)]
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load GovDOC OCR package")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["govdoc_ocr"] = module
    spec.loader.exec_module(module)
    return module


_service_module = _service()
process_pdf_bytes = _service_module.process_pdf_bytes
process_image = _service_module.process_image

# Cache is deliberately process-local. It avoids duplicate OCR work inside a
# single pipeline invocation without changing the pipeline's durable storage.
_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LAST_RESULT: dict[str, Any] | None = None
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def _suffix_from_bytes(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return ".tif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return ".pdf"


def _run(data: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    global _LAST_RESULT
    key = (hashlib.sha256(data).hexdigest(), Path(filename).name)
    if key in _CACHE:
        _LAST_RESULT = _CACHE[key]
        return _LAST_RESULT

    suffix = Path(filename).suffix.lower()
    if suffix not in _IMAGE_SUFFIXES and filename == "document.pdf":
        suffix = _suffix_from_bytes(data)
    if suffix in _IMAGE_SUFFIXES:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / f"document{suffix}"
            image_path.write_bytes(data)
            result = process_image(str(image_path), tmp)
    else:
        result = process_pdf_bytes(data, filename)
    _CACHE[key] = result
    _LAST_RESULT = result
    return result


def _category(info: dict[str, Any]) -> tuple[str, str, str]:
    dtype = info.get("document_type") or {}
    value = dtype.get("value") or "other"
    labels = {
        "admission": "Admission",
        "examination": "Examination",
        "transfer": "Transfer",
        "service": "Service",
        "training": "Training",
        "scholarship": "Scholarship",
        "holiday": "Holiday",
        "other": "Other",
    }
    return value, labels.get(value, value.replace("_", " ").title()), dtype.get("confidence", "LOW")


def _provenance(result: dict[str, Any]) -> dict[str, Any]:
    ocr = result.get("ocr") or {}
    return {
        "service": "GovDOC Vision",
        "service_version": result.get("ocr_service_version"),
        "extraction_method": result.get("extraction_method"),
        "backend": ocr.get("backend"),
        "language": ocr.get("language"),
        "page_count": len(result.get("pages") or []),
    }


def install(processor_module) -> None:
    original_embedded = processor_module.embedded_pdf_text
    original_ocr = processor_module.ocr_pdf
    original_metadata = processor_module.extract_metadata
    original_insert = processor_module.db_insert
    original_patch = processor_module.db_patch
    original_process = processor_module.process

    def embedded(data):
        try:
            result = _run(data)
            return result["text"] if "embedded-text" in result["extraction_method"] else ""
        except Exception:
            return original_embedded(data)

    def ocr(data, workdir):
        try:
            return _run(data)["text"]
        except Exception:
            return original_ocr(data, workdir)

    def metadata(text, filename):
        legacy = original_metadata(text, filename)
        if _LAST_RESULT is None or _LAST_RESULT.get("text") != text:
            return legacy
        info = _LAST_RESULT.get("metadata") or {}
        subject = (info.get("subject") or {}).get("value") or legacy[0]
        authority = (info.get("authority") or {}).get("value") or legacy[1]
        short = _LAST_RESULT.get("short_description") or legacy[5]
        category_key, category, category_confidence = _category(info)
        confidence = "HIGH" if category_confidence == "HIGH" and subject and authority else legacy[9]
        return (
            subject,
            authority,
            legacy[2],
            legacy[3],
            legacy[4],
            short,
            legacy[6],
            category_key,
            category,
            confidence,
        )

    def insert(table, payload):
        if table == "documents" and _LAST_RESULT is not None:
            payload = dict(payload)
            payload["extraction_method"] = _LAST_RESULT.get("extraction_method") or payload.get("extraction_method")
        return original_insert(table, payload)

    def patch(table, rid, payload):
        if table == "telegram_intake" and payload.get("status") == "Processed" and _LAST_RESULT is not None:
            payload = dict(payload)
            metadata = dict(payload.get("metadata") or {})
            metadata["govdoc_ocr"] = _provenance(_LAST_RESULT)
            payload["metadata"] = metadata
        return original_patch(table, rid, payload)

    def process(row):
        global _LAST_RESULT
        _LAST_RESULT = None
        return original_process(row)

    processor_module.embedded_pdf_text = embedded
    processor_module.ocr_pdf = ocr
    processor_module.extract_metadata = metadata
    processor_module.db_insert = insert
    processor_module.db_patch = patch
    processor_module.process = process
