"""Authoritative bridge from the document pipeline to GovDOC Vision.

GovDOC Vision is the canonical OCR engine for production document processing.
Legacy Tesseract extraction is intentionally not used as a silent fallback.
If GovDOC fails, the processing attempt fails explicitly instead of being
mislabelled as GovDOC.
"""
from __future__ import annotations
import hashlib, importlib.util, tempfile
from pathlib import Path
from typing import Any

_SERVICE_RESULT: dict[str, Any] | None = None

def _service():
    root = Path(__file__).resolve().parents[2] / "govdoc-ocr"
    init = root / "__init__.py"
    spec = importlib.util.spec_from_file_location("govdoc_ocr", init, submodule_search_locations=[str(root)])
    if spec is None or spec.loader is None: raise ImportError("Unable to load GovDOC OCR package")
    module = importlib.util.module_from_spec(spec)
    import sys; sys.modules["govdoc_ocr"] = module; spec.loader.exec_module(module)
    return module

_service_module = _service()
process_pdf_bytes = _service_module.process_pdf_bytes
process_image = _service_module.process_image
_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

def _suffix_from_bytes(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"): return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return ".png"
    if data.startswith((b"II*\x00", b"MM\x00*")): return ".tif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP": return ".webp"
    return ".pdf"

def _run(data: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    global _SERVICE_RESULT
    key = (hashlib.sha256(data).hexdigest(), Path(filename).name)
    if key in _CACHE: _SERVICE_RESULT = _CACHE[key]; return _CACHE[key]
    suffix = Path(filename).suffix.lower()
    if suffix not in _IMAGE_SUFFIXES and filename == "document.pdf": suffix = _suffix_from_bytes(data)
    if suffix in _IMAGE_SUFFIXES:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / f"document{suffix}"; image_path.write_bytes(data); result = process_image(str(image_path), tmp)
    else: result = process_pdf_bytes(data, filename)
    _CACHE[key] = result; _SERVICE_RESULT = result; return result

def _category(info: dict[str, Any]) -> tuple[str, str, str]:
    dtype = info.get("document_type") or {}; value = dtype.get("value") or "other"
    labels = {"admission":"Admission","examination":"Examination","transfer":"Transfer","service":"Service","training":"Training","scholarship":"Scholarship","holiday":"Holiday","other":"Other"}
    return value, labels.get(value, value), dtype.get("confidence", "LOW")

def install(processor_module) -> None:
    original_metadata = processor_module.extract_metadata
    original_insert = getattr(processor_module, "db_insert", None)
    def embedded(data, filename="document.pdf"):
        result = _run(data, filename)
        return result["text"] if "embedded-text" in result.get("extraction_method", "") else ""
    def ocr(data, workdir, filename="document.pdf"): return _run(data, filename)["text"]
    def metadata(text, filename):
        legacy = original_metadata(text, filename); result = _SERVICE_RESULT
        if not result or result.get("text") != text: return legacy
        info = result.get("metadata") or {}; subject = (info.get("subject") or {}).get("value") or legacy[0]; authority = (info.get("authority") or {}).get("value") or legacy[1]; short = result.get("short_description") or legacy[5]
        category_key, category, category_confidence = _category(info); confidence = "HIGH" if category_confidence == "HIGH" and subject and authority else legacy[9]
        return (subject, authority, legacy[2], legacy[3], legacy[4], short, legacy[6], category_key, category, confidence)
    processor_module.embedded_pdf_text = embedded; processor_module.ocr_pdf = ocr; processor_module.extract_metadata = metadata
    if callable(original_insert):
        def insert(table, payload):
            result = _SERVICE_RESULT
            if table == "documents" and result:
                enriched = dict(payload); enriched["extraction_method"] = result.get("extraction_method") or enriched.get("extraction_method"); enriched["extraction_confidence"] = enriched.get("extraction_confidence") or "MEDIUM"; enriched["category_source"] = "GovDOC Vision"; enriched["category_confidence"] = ((result.get("metadata") or {}).get("document_type") or {}).get("confidence"); enriched["ai_model"] = None; enriched["ai_suggested_json"] = result.get("metadata"); return original_insert(table, enriched)
            return original_insert(table, payload)
        processor_module.db_insert = insert
