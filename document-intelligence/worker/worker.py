from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import boto3
from supabase import create_client

from govdoc_ocr.ocr_service import process_document
from ai_enrichment import enrich


def env(name: str) -> str:
    value = os.getenv(name)
    if not value: raise RuntimeError(f"Missing environment variable: {name}")
    return value


def clients():
    db = create_client(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"))
    s3 = boto3.client("s3", endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com", aws_access_key_id=env("R2_ACCESS_KEY_ID"), aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"), region_name="auto")
    return db, s3


def claim(db):
    result = db.rpc("claim_next_document", {}).execute()
    return result.data[0] if result.data else None


def evidence_images(source: Path, tmp: str) -> list[str]:
    if not os.getenv("GEMINI_API_KEY") or source.suffix.lower() != ".pdf": return []
    maximum = max(1, min(3, int(os.getenv("GEMINI_EVIDENCE_PAGES", "2"))))
    prefix = Path(tmp) / "ai-page"
    subprocess.run(["pdftoppm", "-f", "1", "-l", str(maximum), "-r", "160", "-jpeg", str(source), str(prefix)], check=True, capture_output=True, timeout=120)
    return [str(path) for path in sorted(Path(tmp).glob("ai-page-*.jpg"))]


def process_one(db, s3, row):
    document_id, key, filename = row["id"], row["source_key"], row["original_filename"]
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / Path(filename).name
        s3.download_file(env("R2_BUCKET"), key, str(source))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        result = process_document(str(source), tmp, backend="tesseract")
        metadata = result.get("metadata") or {}
        pages = result.get("pages", [])
        ai = None
        if os.getenv("GEMINI_API_KEY"):
            try:
                ai = enrich(result.get("text", ""), metadata, evidence_images(source, tmp))
            except Exception as exc:
                db.table("document_audit").insert({"document_id": document_id, "event_type": "ai_enrichment_failed", "details": {"error_type": type(exc).__name__}}).execute()
        low_confidence = any((p.get("confidence") is not None and float(p["confidence"]) < 70) or not p.get("text", "").strip() for p in pages if p.get("extraction_method", "").startswith("ocr:"))
        extracted = {"schema_version": result.get("schema_version"), "filename": filename, "source_key": key, "extraction_method": result.get("extraction_method"), "metadata": metadata, "ai_enrichment": ai, "pages": pages, "ocr": result.get("ocr", {})}
        status = "review_required" if low_confidence or bool(ai and ai.get("review_fields")) else "verified"
        final_subject = (ai or {}).get("subject") or result.get("subject") or None
        final_type = (ai or {}).get("document_type") or result.get("category") or None
        final_authority = (ai or {}).get("issuing_authority") or result.get("authority") or None
        final_date = (ai or {}).get("document_date") or None
        final_ref = (ai or {}).get("reference_number") or None
        final_description = (ai or {}).get("description") or result.get("short_description") or None
        db.table("documents").update({"sha256": digest, "status": status, "document_type": final_type, "subject": final_subject, "issuing_authority": final_authority, "document_date": final_date, "reference_number": final_ref, "description": final_description, "language": "hi+en", "raw_ocr": result.get("text") or "", "ai_summary": (ai or {}).get("description"), "extraction_json": extracted, "confidence_json": {"pages": [p.get("confidence") for p in pages], "ai_review_fields": (ai or {}).get("review_fields", [])}}).eq("id", document_id).execute()
        page_rows = [{"document_id": document_id, "page_number": p["page_number"], "source_key": key, "extraction_method": p.get("extraction_method"), "raw_ocr": p.get("text", ""), "normalized_text": p.get("text", ""), "regions": p.get("regions", []), "diagnostics": {"diagnostics": p.get("diagnostics"), "visual_marks": p.get("visual_marks"), "handwriting_review": p.get("handwriting_review")}} for p in pages]
        if page_rows: db.table("document_pages").upsert(page_rows, on_conflict="document_id,page_number").execute()
        db.table("document_audit").insert({"document_id": document_id, "event_type": "ocr_completed", "details": {"status": status, "sha256": digest, "page_count": len(pages), "ai_enrichment": ai is not None}}).execute()


def main():
    db, s3 = clients(); maximum = max(1, int(os.getenv("MAX_DOCUMENTS_PER_RUN", "5"))); processed = 0
    for _ in range(maximum):
        row = claim(db)
        if not row: break
        try:
            process_one(db, s3, row); processed += 1; print(json.dumps({"processed": row["id"]}))
        except Exception as exc:
            db.table("documents").update({"status": "failed"}).eq("id", row["id"]).execute()
            db.table("document_audit").insert({"document_id": row["id"], "event_type": "ocr_failed", "details": {"error_type": type(exc).__name__}}).execute()
            print(json.dumps({"failed": row["id"], "error_type": type(exc).__name__}))
    print(json.dumps({"batch_processed": processed, "batch_limit": maximum}))


if __name__ == "__main__": main()
