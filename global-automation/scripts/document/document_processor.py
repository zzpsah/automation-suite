#!/usr/bin/env python3
"""Process stored Telegram documents into the Supabase documents index.

B2 is the source file store. Google Drive remains backup. OCR uses Tesseract
with Hindi + English language data and falls back to embedded PDF text first.
Processing is deliberately non-blocking: extraction failures become
Needs Manual Review rather than losing the source record.
"""
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
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload, timeout=30,
    )
    r.raise_for_status()


def db_insert_document(payload):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/documents",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=representation"},
        json=payload, timeout=30,
    )
    r.raise_for_status()
    return r.json()[0] if r.json() else {}


def b2_client():
    return boto3.client("s3", endpoint_url=B2_ENDPOINT, region_name="us-east-005",
                        aws_access_key_id=B2_KEY_ID, aws_secret_access_key=B2_APP_KEY)


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def embedded_pdf_text(data):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    except Exception:
        return ""


def ocr_pdf(data, workdir):
    pdf = Path(workdir) / "input.pdf"
    pdf.write_bytes(data)
    prefix = Path(workdir) / "page"
    import subprocess
    subprocess.run(["pdftoppm", "-r", "250", "-jpeg", str(pdf), str(prefix)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
    images = sorted(Path(workdir).glob("page-*.jpg"))
    if not images:
        raise RuntimeError("PDF rendering produced no pages")
    chunks = []
    for image in images:
        p = subprocess.run(["tesseract", str(image), "stdout", "-l", "hin+eng", "--psm", "6"],
                           capture_output=True, text=True, timeout=180)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-500:] or "Tesseract failed")
        chunks.append(p.stdout)
    return clean_text("\n\n".join(chunks))


def first_match(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            value = m.group(1).strip(" :-–—\t")
            if value:
                return value[:500]
    return ""


def extract_metadata(text, filename):
    # Hindi/English labels commonly found in departmental letters.
    subject = first_match(text, [
        r"(?:विषय|विषय\s*:-|subject|sub\.)\s*[:\-–—]?\s*(.+)",
    ])
    authority = first_match(text, [
        r"(?:प्रेषक|जारीकर्ता|कार्यालय|सेवा में|issuing authority|from)\s*[:\-–—]?\s*(.+)",
    ])
    ref_no = first_match(text, [
        r"(?:पत्रांक|पत्र\s*संख्या|पत्र\s*सं\.|क्रमांक|reference\s*(?:no|number)|memo\s*no)\s*[:\-–—]?\s*([^\n]+)",
    ])
    date = first_match(text, [
        r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+\d{4})\b",
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
    ])
    if not subject:
        # Keep the first useful line as a provisional subject, never a giant OCR blob.
        for line in text.splitlines():
            line = line.strip()
            if 12 <= len(line) <= 180 and not re.fullmatch(r"[\d\W]+", line):
                subject = line
                break
    if not authority:
        authority = ""
    short = subject or filename or "Document"
    summary = " ".join(text.split())[:3000]
    detailed = (f"यह दस्तावेज़ {filename} के रूप में प्राप्त हुआ। "
                + (f"विषय: {subject}. " if subject else "विषय स्वतः निर्धारित नहीं हो सका। ")
                + (f"जारीकर्ता: {authority}. " if authority else "जारीकर्ता स्वतः निर्धारित नहीं हो सका। ")
                + (f"जारी तिथि: {date}. " if date else "जारी तिथि स्वतः निर्धारित नहीं हो सकी। ")
                + "OCR से प्राप्त पाठ के आधार पर विवरण तैयार किया गया है।")
    return {
        "subject": subject[:1000],
        "issuing_authority": authority[:500],
        "reference_number": ref_no[:250],
        "issued_date": date,
        "short_description": short[:500],
        "detailed_summary": detailed[:4000],
        "full_text_ocr": text,
    }


def process(row):
    record_id = row["id"]
    metadata = row.get("metadata") or {}
    storage = metadata.get("storage") or {}
    key = storage.get("b2_key")
    if not key or storage.get("b2_status") != "AVAILABLE":
        raise RuntimeError("Stored record has no verified B2 object")

    # Idempotency: don't create a second documents row for the same intake record.
    existing = db_get(f"documents?select=id&source_reference=eq.{record_id}&limit=1")
    if existing:
        db_patch("telegram_intake", record_id, {"status": "Processed", "metadata": {**metadata, "document_id": existing[0]["id"]}})
        return False

    s3 = b2_client()
    obj = s3.get_object(Bucket=B2_BUCKET, Key=key)
    data = obj["Body"].read()
    if not data:
        raise RuntimeError("B2 object is empty")

    with tempfile.TemporaryDirectory() as workdir:
        text = embedded_pdf_text(data)
        # Scanned PDFs normally have little/no embedded text.
        if len(re.sub(r"\s+", "", text)) < 80:
            text = ocr_pdf(data, workdir)

    if not text:
        raise RuntimeError("No text could be extracted from PDF")

    extracted = extract_metadata(text, row.get("file_name") or "document")
    confidence = "HIGH" if extracted["subject"] and extracted["issued_date"] else "MEDIUM"
    payload = {
        "id": str(uuid.uuid4()),
        "source_reference": str(record_id),
        "file_name": row.get("file_name"),
        "mime_type": row.get("mime_type"),
        "received_at": row.get("received_at"),
        "subject": extracted["subject"] or "",
        "issuing_authority": extracted["issuing_authority"] or "",
        "reference_number": extracted["reference_number"] or "",
        "issued_date": extracted["issued_date"] or None,
        "short_description": extracted["short_description"],
        "detailed_summary": extracted["detailed_summary"],
        "full_text_ocr": extracted["full_text_ocr"],
        "extraction_confidence": confidence,
        "category_confidence": "LOW",
        "processing_status": "Completed",
        "publication_status": "Unpublished",
        "category_source": "manual",
        "ai_suggestion_status": "Not Requested",
        "forwarding_status": "Not Forwarded",
        "priority": "NORMAL",
        "public_file_url": "",
    }
    try:
        created = db_insert_document(payload)
    except requests.HTTPError as exc:
        # Some deployments may not have all optional columns; retry with the core schema fields.
        if exc.response is None or exc.response.status_code < 400:
            raise
        core = {k: v for k, v in payload.items() if k not in {"file_name", "mime_type", "reference_number", "public_file_url"}}
        created = db_insert_document(core)

    doc_id = created.get("id") or payload["id"]
    db_patch("telegram_intake", record_id, {"status": "Processed", "metadata": {**metadata, "document_id": doc_id, "processed_at": datetime.now(timezone.utc).isoformat()}})
    print(f"Processed {record_id} -> document {doc_id}")
    return True


def main():
    rows = db_get("telegram_intake?select=*&status.eq.Stored&order=received_at.asc&limit=10")
    processed = failed = 0
    for row in rows:
        try:
            if process(row):
                processed += 1
        except Exception as exc:
            failed += 1
            metadata = row.get("metadata") or {}
            db_patch("telegram_intake", row["id"], {"status": "Processing Failed", "metadata": {**metadata, "processing_error": str(exc)[:500], "processing_error_at": datetime.now(timezone.utc).isoformat()}})
            print(f"Record {row['id']}: processing failed: {exc}")
    print(f"Document processor complete: processed={processed}, failed={failed}, candidates={len(rows)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
