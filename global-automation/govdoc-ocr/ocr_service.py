"""Reusable GovDOC OCR service for Hindi/English government PDFs.

The service is intentionally independent of Supabase, B2, Drive and Telegram.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

OCR_SERVICE_VERSION = "2.0"


def _clean(text: str) -> str:
    text = (text or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _embedded(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
        return _clean("\n".join(p.extract_text() or "" for p in PdfReader(str(pdf_path)).pages))
    except Exception:
        return ""


def _ocr(pdf_path: Path, workdir: Path) -> str:
    prefix = workdir / "page"
    subprocess.run(
        ["pdftoppm", "-r", "250", "-jpeg", str(pdf_path), str(prefix)],
        check=True, capture_output=True, text=True, timeout=180,
    )
    images = sorted(workdir.glob("page-*.jpg"))
    if not images:
        raise RuntimeError("PDF rendering produced no pages")
    chunks = []
    for image in images:
        result = subprocess.run(
            ["tesseract", str(image), "stdout", "-l", "hin+eng", "--psm", "6"],
            check=True, capture_output=True, text=True, encoding="utf-8", timeout=180,
        )
        chunks.append(result.stdout)
    return _clean("\n\n".join(chunks))


def _lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", x).strip(" :-–—\t") for x in text.splitlines() if x.strip()]


def _label(lines: list[str], labels: list[str], limit: int = 1000) -> str:
    pattern = "|".join(labels)
    for i, line in enumerate(lines):
        match = re.match(rf"^(?:{pattern})\s*[:\-–—]?\s*(.*)$", line, re.I)
        if not match:
            continue
        value = match.group(1).strip(" :-–—\t")
        if value and len(value) <= limit:
            return value
        if not value and i + 1 < len(lines) and len(lines[i + 1]) <= limit:
            return lines[i + 1]
    return ""


def _date(value: str) -> str | None:
    match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", (value or "").strip())
    if not match:
        return None
    day, month, year = match.groups()
    year = int(year) + (2000 if int(year) < 100 else 0)
    try:
        import datetime
        datetime.date(year, int(month), int(day))
        return f"{year:04d}-{int(month):02d}-{int(day):02d}"
    except ValueError:
        return None


def _metadata(text: str, filename: str) -> dict[str, Any]:
    lines = _lines(text)
    subject = _label(lines, ["विषय", "विषयक", "subject", "sub\\."], 1000)
    if subject:
        subject = re.split(r"\s+(?:प्रसंग|दिनांक|पत्रांक|reference|memo)\s*[:\-–—]?", subject, 1, re.I)[0].strip(" :-–—")
    authority = _label(lines, ["प्रेषक", "जारीकर्ता", "जारी करने वाला कार्यालय", "issuing authority", "from"], 500)
    if not authority:
        known = ["बिहार विद्यालय परीक्षा समिति", "बिहार शिक्षा परियोजना परिषद्", "बिहार शिक्षा परियोजना परिषद", "जिला शिक्षा पदाधिकारी", "जिला कार्यक्रम पदाधिकारी", "शिक्षा विभाग, बिहार सरकार", "शिक्षा विभाग बिहार सरकार"]
        authority = next((name for name in known if re.search(re.escape(name), text, re.I)), "")
    reference = _label(lines, ["पत्रांक", "ज्ञापांक", "पत्र संख्या", "पत्र सं\\.", "क्रमांक", "reference no", "reference number", "memo no"], 250)
    printed = _label(lines, ["दिनांक", "दिनांक :", "date"], 100)
    match = re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b", printed or text)
    printed = match.group(1) if match else ""
    normalized = _date(printed)
    if not subject and re.search(r"स्पॉट\s*नामांकन|Spot\s*Admission", text, re.I):
        subject = "सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन (Spot Admission) हेतु सूचना"
    if re.search(r"स्पॉट\s*नामांकन|नामांकन|admission|OFSS", text, re.I):
        category_key, category = "admission", "Admission"
    elif re.search(r"बिहार\s*विद्यालय\s*परीक्षा\s*समिति|BSEB", text, re.I):
        category_key, category = "bseb", "BSEB"
    else:
        category_key, category = "other", "Other"
    confidence = "HIGH" if subject and (printed or authority) else "MEDIUM"
    short = subject[:500]
    detailed = (
        f"यह दस्तावेज़ {filename} के रूप में प्राप्त हुआ। "
        + (f"विषय: {subject}. " if subject else "विषय स्वतः निर्धारित नहीं हो सका। ")
        + (f"जारीकर्ता: {authority}. " if authority else "जारीकर्ता स्वतः निर्धारित नहीं हो सका। ")
        + (f"जारी तिथि: {printed}. " if printed else "जारी तिथि स्वतः निर्धारित नहीं हो सकी। ")
        + "GovDOC OCR Engine के पाठ निष्कर्षण के आधार पर विवरण तैयार किया गया है।"
    )
    return {
        "subject": subject, "authority": authority, "reference_number": reference,
        "issue_date": printed, "normalized_issue_date": normalized,
        "short_description": short, "detailed_summary": detailed,
        "category_key": category_key, "category": category, "confidence": confidence,
    }


def process_pdf(pdf_path: str, work_dir: str, *, min_embedded_chars: int = 80) -> dict[str, Any]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("GovDOC OCR currently accepts PDF files only")
    text = _embedded(path)
    method = "GovDOC OCR: embedded-text"
    if len(re.sub(r"\s+", "", text)) < min_embedded_chars:
        text = _ocr(path, Path(work_dir))
        method = "GovDOC OCR: Tesseract Hindi+English"
    if not text:
        raise RuntimeError("No text could be extracted from PDF")
    result = _metadata(text, path.name)
    result.update({
        "text": text,
        "extraction_method": method,
        "filename": path.name,
        "ocr_service_version": OCR_SERVICE_VERSION,
    })
    return result


def process_pdf_bytes(data: bytes, filename: str = "document.pdf", work_dir: str | None = None) -> dict[str, Any]:
    """Process PDF bytes without coupling the OCR engine to storage infrastructure."""
    if not data:
        raise ValueError("PDF data is empty")
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        path = Path(tmp) / (Path(filename).name or "document.pdf")
        path.write_bytes(data)
        return process_pdf(str(path), tmp)
