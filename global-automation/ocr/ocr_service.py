"""Stable, project-agnostic public interface for Global Sarkari OCR."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .diagnostics import diagnose_pages
from .language_packs.bihar_office_resolver import resolve_office
from .ocr_engine import extract_document_pages, ocr_image_detailed
from .sarkari_normalizer import extract_metadata
from .subject_extractor import extract_multiline_subject
from .taxonomy import taxonomy_info

OCR_SERVICE_VERSION = "1.5"
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def score_metadata_quality(metadata: dict[str, Any], text: str) -> dict[str, Any]:
    checks = {}
    subject, authority = metadata.get("subject"), metadata.get("authority")
    reference, date = metadata.get("reference_number"), metadata.get("issue_date")
    checks["subject"] = bool(subject and 8 <= len(subject.strip()) <= 1200)
    checks["authority"] = bool(authority and 3 <= len(authority.strip()) <= 300)
    checks["reference_number"] = bool(reference and 1 <= len(reference.strip()) <= 250)
    checks["issue_date"] = bool(date and len(date) == 10 and date[4] == "-" and date[7] == "-")
    evidence_text = (text or "").casefold()
    evidence = {name: bool(value and str(value).casefold() in evidence_text) for name, value in {
        "subject": subject, "authority": authority, "reference_number": reference, "issue_date": date
    }.items()}
    weights = {"subject": 0.30, "authority": 0.30, "reference_number": 0.15, "issue_date": 0.25}
    total = sum(weights[k] for k in checks if checks[k] and evidence[k])
    level = "HIGH" if total >= 0.80 else "MEDIUM" if total >= 0.45 else "LOW"
    return {"level": level, "score": round(total, 2), "fields": checks, "evidence": evidence}


def _assemble_result(path: Path, text: str, *, method: str, page_texts: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = extract_metadata(text)
    result = asdict(metadata)
    subject = extract_multiline_subject(text)
    if subject:
        result["subject"] = subject
    result["confidence_details"] = score_metadata_quality(result, text)
    result["confidence"] = result["confidence_details"]["level"]
    result["taxonomy"] = taxonomy_info(result.get("category"))
    result["bihar_office"] = resolve_office(text)
    result["page_diagnostics"] = diagnose_pages(page_texts)
    result["pages"] = [{"page_number": i, "text": page} for i, page in enumerate(page_texts, 1)]
    result.update({"text": text, "extraction_method": method, "filename": path.name, "ocr_service_version": OCR_SERVICE_VERSION})
    if extra:
        result.update(extra)
    return result


def process_pdf(pdf_path: str, work_dir: str, *, min_embedded_chars: int = 80) -> dict[str, Any]:
    """Process a PDF without project/database dependencies."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("process_pdf accepts PDF files only")
    page_texts, method = extract_document_pages(str(path), work_dir, min_embedded_chars=min_embedded_chars)
    text = "\n\n".join(page_texts)
    return _assemble_result(path, text, method=method, page_texts=page_texts)


def process_image(image_path: str, work_dir: str, *, language: str = "hin+eng", psm: int = 6, strategy: str = "auto") -> dict[str, Any]:
    """Process a standalone image using quality-aware preprocessing."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(image_path)
    if path.suffix.lower() not in _IMAGE_SUFFIXES:
        raise ValueError("process_image accepts common raster image files only")
    ocr = ocr_image_detailed(str(path), lang=language, psm=psm, strategy=strategy)
    return _assemble_result(path, ocr["text"], method="tesseract-image-quality-aware", page_texts=[ocr["text"]], extra={"ocr": ocr})


def process_file(file_path: str, work_dir: str, *, min_embedded_chars: int = 80, language: str = "hin+eng", psm: int = 6, strategy: str = "auto") -> dict[str, Any]:
    """Process either a PDF or image through the same stable consumer API."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return process_pdf(file_path, work_dir, min_embedded_chars=min_embedded_chars)
    if suffix in _IMAGE_SUFFIXES:
        return process_image(file_path, work_dir, language=language, psm=psm, strategy=strategy)
    raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")
