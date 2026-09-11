#!/usr/bin/env python3
"""B2 -> OCR -> Supabase documents processor for Telegram intake."""
import io
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")
B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_patch(table, record_id, payload):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}", headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"}, json=payload, timeout=30)
    r.raise_for_status()


def db_insert(payload):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/documents", headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=representation"}, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}


def b2_client():
    return boto3.client("s3", endpoint_url=B2_ENDPOINT, region_name="us-east-005", aws_access_key_id=B2_KEY_ID, aws_secret_access_key=B2_APP_KEY)


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def embedded_pdf_text(data):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    except Exception:
        return ""


def ocr_pdf(data, workdir):
    import subprocess
    pdf = Path(workdir) / "input.pdf"
    pdf.write_bytes(data)
    prefix = Path(workdir) / "page"
    subprocess.run(["pdftoppm", "-r", "250", "-jpeg", str(pdf), str(prefix)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
    images = sorted(Path(workdir).glob("page-*.jpg"))
    if not images:
        raise RuntimeError("PDF rendering produced no pages")
    chunks = []
    for image in images:
        p = subprocess.run(["tesseract", str(image), "stdout", "-l", "hin+eng", "--psm", "6"], capture_output=True, text=True, timeout=180)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-500:] or "Tesseract failed")
        chunks.append(p.stdout)
    return clean_text("\n\n".join(chunks))


def first_match(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m and m.group(1).strip():
            return m.group(1).strip(" :-–—\t")[:500]
    return ""


def normalize_date(value):
    if not value:
        return None
    m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", value.strip())
    if m:
        d, mo, y = m.groups()
        y = int(y) + (2000 if int(y) < 100 else 0)
        try:
            return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
        except ValueError:
            return None
    return None


def extract_metadata(text, filename):
    subject = first_match(text, [r"(?:विषय|subject|sub\.)\s*[:\-–—]?\s*(.+)"])
    authority = first_match(text, [r"(?:प्रेषक|जारीकर्ता|कार्यालय|issuing authority|from)\s*[:\-–—]?\s*(.+)"])
    ref_no = first_match(text, [r"(?:पत्रांक|पत्र\s*संख्या|पत्र\s*सं\.|क्रमांक|reference\s*(?:no|number)|memo\s*no)\s*[:\-–—]?\s*([^\n]+)"])
    printed_date = first_match(text, [r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", r"(\d{1,2}\s+(?:जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+\d{4})", r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"])
    if not subject:
        for line in text.splitlines():
            line = line.strip()
            if 12 <= len(line) <= 180 and not re.fullmatch(r"[\d\W]+", line):
                subject = line
                break
    short = subject or filename or "दस्तावेज़"
    detailed = (f"यह दस्तावेज़ {filename} के रूप में प्राप्त हुआ। " + (f"विषय: {subject}. " if subject else "विषय स्वतः निर्धारित नहीं हो सका। ") + (f"जारीकर्ता: {authority}. " if authority else "जारीकर्ता स्वतः निर्धारित नहीं हो सका। ") + (f"जारी तिथि: {printed_date}. " if printed_date else "जारी तिथि स्वतः निर्धारित नहीं हो सकी। ") + "OCR/पाठ निष्कर्षण के आधार पर विवरण तैयार किया गया है।")
    return subject[:1000], authority[:500], ref_no[:250], printed_date, normalize_date(printed_date), short[:500], detailed[:4000]


def process(row):
    rid = row["id"]
    metadata = row.get("metadata") or {}
    storage = metadata.get("storage") or {}
    key = storage.get("b2_key")
    if not key or storage.get("b2_status") != "AVAILABLE":
        raise RuntimeError("Verified B2 object is missing")
    existing = db_get(f"documents?select=id&source_app=eq.UMVInputBot&source_message_id=eq.{rid}&limit=1")
    if existing:
        db_patch("telegram_intake", rid, {"status": "Processed", "metadata": {**metadata, "document_id": existing[0]["id"]}})
        return False
    data = b2_client().get_object(Bucket=B2_BUCKET, Key=key)["Body"].read()
    if not data:
        raise RuntimeError("B2 object is empty")
    with tempfile.TemporaryDirectory() as workdir:
        text = embedded_pdf_text(data)
        method = "Embedded PDF text"
        if len(re.sub(r"\s+", "", text)) < 80:
            text = ocr_pdf(data, workdir)
            method = "Tesseract OCR (Hindi+English)"
    if not text:
        raise RuntimeError("No text could be extracted from PDF")
    subject, authority, ref_no, printed_date, normalized_date, short, detailed = extract_metadata(text, row.get("file_name") or "document")
    confidence = "HIGH" if subject and printed_date else "MEDIUM"
    doc_id = str(uuid.uuid4())
    payload = {
        "id": doc_id, "source_app": "UMVInputBot", "source_location": "Telegram", "source_message_id": str(rid),
        "original_filename": row.get("file_name"), "display_filename": row.get("file_name"), "mime_type": row.get("mime_type"),
        "file_size": len(data), "file_checksum": storage.get("sha256"), "private_drive_file_id": storage.get("drive_file_id"),
        "private_drive_url": (f"https://drive.google.com/file/d/{storage.get('drive_file_id')}/view" if storage.get("drive_file_id") else None),
        "public_file_url": "", "reference_number": ref_no or None, "issue_date_as_printed": printed_date or None,
        "normalized_issue_date": normalized_date, "received_at": row.get("received_at"), "issuing_authority": authority or None,
        "subject": subject or None, "short_description": short, "detailed_summary": detailed,
        "category": "Other", "subcategory": None, "priority": "NORMAL", "required_action": "None",
        "deadline_as_printed": None, "normalized_deadline": None, "affected_entities": [], "financial_amount": None,
        "full_text_ocr": text, "extraction_method": method, "extraction_confidence": confidence, "sensitive": False,
        "useful": True, "duplicate": False, "duplicate_reason": None, "processing_status": "Completed",
        "forwarding_status": "Not Forwarded", "approved_for_publication": False, "category_key": "other",
        "category_source": "rule", "category_confidence": "LOW", "ai_suggestion_status": "Not Requested",
        "ai_model": None, "ai_suggested_title": None, "ai_suggested_display_filename": None, "ai_suggested_description": None,
        "ai_suggested_json": None, "ai_suggested_at": None, "publication_status": "Unpublished",
        "publication_reason": "Awaiting publication workflow", "unpublished_at": None, "source_file_modified_at": None, "public_revision": 0,
    }
    created = db_insert(payload)
    actual_id = created.get("id", doc_id)
    db_patch("telegram_intake", rid, {"status": "Processed", "metadata": {**metadata, "document_id": actual_id, "processed_at": datetime.now(timezone.utc).isoformat()}})
    print(f"Processed {rid} -> {actual_id} via {method}")
    return True


def main():
    rows = db_get("telegram_intake?select=*&status.eq.Stored&order=received_at.asc&limit=10")
    processed = failed = 0
    for row in rows:
        try:
            if process(row): processed += 1
        except Exception as exc:
            failed += 1
            md = row.get("metadata") or {}
            db_patch("telegram_intake", row["id"], {"status": "Processing Failed", "metadata": {**md, "processing_error": str(exc)[:500], "processing_error_at": datetime.now(timezone.utc).isoformat()}})
            print(f"Record {row['id']}: processing failed: {exc}")
    print(f"Document processor complete: processed={processed}, failed={failed}, candidates={len(rows)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
