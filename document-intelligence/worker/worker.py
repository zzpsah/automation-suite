from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import boto3
from supabase import create_client

from govdoc_ocr.ocr_service import process_document


def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def clients():
    db = create_client(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"))
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )
    return db, s3


def claim(db):
    result = db.rpc("claim_next_document", {}).execute()
    return result.data[0] if result.data else None


def process_one(db, s3, row):
    document_id = row["id"]
    key = row["source_key"]
    filename = row["original_filename"]
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / Path(filename).name
        s3.download_file(env("R2_BUCKET"), key, str(source))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        result = process_document(str(source), tmp, backend="tesseract")
        metadata = result.get("metadata") or {}
        extracted = {
            "schema_version": result.get("schema_version"),
            "filename": filename,
            "source_key": key,
            "extraction_method": result.get("extraction_method"),
            "metadata": metadata,
            "pages": result.get("pages", []),
            "ocr": result.get("ocr", {}),
        }
        status = "review_required" if any(
            (p.get("confidence") is not None and float(p["confidence"]) < 70) or not p.get("text", "").strip()
            for p in result.get("pages", []) if p.get("extraction_method", "").startswith("ocr:")
        ) else "verified"
        update = {
            "sha256": digest,
            "status": status,
            "document_type": result.get("category") or None,
            "subject": result.get("subject") or None,
            "issuing_authority": result.get("authority") or None,
            "description": result.get("short_description") or None,
            "language": "hi+en",
            "raw_ocr": result.get("text") or "",
            "ai_summary": None,
            "extraction_json": extracted,
            "confidence_json": {"pages": [p.get("confidence") for p in result.get("pages", [])]},
        }
        db.table("documents").update(update).eq("id", document_id).execute()
        pages = []
        for page in result.get("pages", []):
            pages.append({
                "document_id": document_id,
                "page_number": page["page_number"],
                "source_key": key,
                "extraction_method": page.get("extraction_method"),
                "raw_ocr": page.get("text", ""),
                "normalized_text": page.get("text", ""),
                "regions": page.get("regions", []),
                "diagnostics": {"diagnostics": page.get("diagnostics"), "visual_marks": page.get("visual_marks"), "handwriting_review": page.get("handwriting_review")},
            })
        if pages:
            db.table("document_pages").upsert(pages, on_conflict="document_id,page_number").execute()
        db.table("document_audit").insert({"document_id": document_id, "event_type": "ocr_completed", "details": {"status": status, "sha256": digest}}).execute()


def main():
    db, s3 = clients()
    row = claim(db)
    if not row:
        print("No queued documents.")
        return
    try:
        process_one(db, s3, row)
        print(json.dumps({"processed": row["id"], "filename": row["original_filename"]}))
    except Exception as exc:
        db.table("documents").update({"status": "failed"}).eq("id", row["id"]).execute()
        db.table("document_audit").insert({"document_id": row["id"], "event_type": "ocr_failed", "details": {"error": str(exc)[:1000]}}).execute()
        raise


if __name__ == "__main__":
    main()
