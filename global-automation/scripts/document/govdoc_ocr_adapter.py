"""Bridge the production document processor to the shared GovDOC Vision engine.

GovDOC owns OCR and government-document intelligence. The existing School
Document Pipeline remains responsible for storage, lifecycle and publication.
Legacy extraction is retained for fields GovDOC does not currently expose.
"""
from __future__ import annotations
import hashlib, importlib.util
from pathlib import Path
from typing import Any


def _service():
    root = Path(__file__).resolve().parents[2] / "govdoc-ocr"
    init = root / "__init__.py"
    spec = importlib.util.spec_from_file_location("govdoc_ocr", init, submodule_search_locations=[str(root)])
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load GovDOC OCR package")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["govdoc_ocr"] = module
    spec.loader.exec_module(module)
    return module


process_pdf_bytes = _service().process_pdf_bytes
_CACHE: dict[str, dict[str, Any]] = {}


def _run(data: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    key = hashlib.sha256(data).hexdigest()
    if key not in _CACHE:
        _CACHE[key] = process_pdf_bytes(data, filename)
    return _CACHE[key]


def _category(info: dict[str, Any]) -> tuple[str, str, str]:
    dtype = info.get("document_type") or {}
    value = dtype.get("value") or "other"
    labels = {"admission":"Admission", "examination":"Examination", "transfer":"Transfer", "service":"Service", "training":"Training", "scholarship":"Scholarship", "holiday":"Holiday", "other":"Other"}
    return value, labels.get(value, value.replace("_", " ").title()), dtype.get("confidence", "LOW")


def install(processor_module) -> None:
    original_embedded = processor_module.embedded_pdf_text
    original_ocr = processor_module.ocr_pdf
    original_metadata = processor_module.extract_metadata

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
        for result in reversed(list(_CACHE.values())):
            if result.get("text") != text:
                continue
            info = result.get("metadata") or {}
            subject = (info.get("subject") or {}).get("value") or legacy[0]
            authority = (info.get("authority") or {}).get("value") or legacy[1]
            short = result.get("short_description") or legacy[5]
            category_key, category, category_confidence = _category(info)
            confidence = "HIGH" if category_confidence == "HIGH" and subject and authority else legacy[9]
            return (subject, authority, legacy[2], legacy[3], legacy[4], short, legacy[6], category_key, category, confidence)
        return legacy

    processor_module.embedded_pdf_text = embedded
    processor_module.ocr_pdf = ocr
    processor_module.extract_metadata = metadata
