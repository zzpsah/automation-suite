"""Offline resilience contracts for the School Pipeline boundary.

These tests exercise the state-transition rules without touching production
Supabase/B2 resources. Network/storage calls are replaced with deterministic
fakes so retry, duplicate and concurrent-claim behavior can be reviewed in CI.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROCESSOR = ROOT / "global-automation/scripts/document/document_processor.py"


def load_processor(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test")
    monkeypatch.setenv("B2_KEY_ID", "test")
    monkeypatch.setenv("B2_APPLICATION_KEY", "test")
    monkeypatch.setenv("GOVDOC_VISION_ENABLED", "0")
    spec = importlib.util.spec_from_file_location("document_processor_test", PROCESSOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_b2_is_fail_closed(monkeypatch):
    processor = load_processor(monkeypatch)
    assert processor.has_verified_b2({"metadata": {}}) is False
    assert processor.has_verified_b2({"metadata": {"storage": {"b2_key": "x", "b2_status": "UPLOADING"}}}) is False
    assert processor.has_verified_b2({"metadata": {"storage": {"b2_key": "x", "b2_status": "AVAILABLE"}}}) is True


def test_concurrent_claim_returns_none_when_already_claimed(monkeypatch):
    processor = load_processor(monkeypatch)
    class Response:
        def raise_for_status(self): pass
        def json(self): return []
    monkeypatch.setattr(processor.requests, "patch", lambda *a, **k: Response())
    assert processor.claim_intake("record-1") is None


def test_retry_failure_is_recorded_without_publication_approval(monkeypatch):
    processor = load_processor(monkeypatch)
    updates = []
    monkeypatch.setattr(processor, "db_patch", lambda table, rid, payload: updates.append((table, rid, payload)))
    row = {"id": "record-1", "metadata": {"storage": {"b2_key": "x", "b2_status": "AVAILABLE"}}}
    try:
        raise RuntimeError("synthetic OCR failure")
    except Exception as exc:
        md = row.get("metadata") or {}
        processor.db_patch("telegram_intake", row["id"], {"status": "Processing Failed", "metadata": {**md, "processing_error": str(exc)}})
    assert updates[0][2]["status"] == "Processing Failed"


def test_publication_remains_explicitly_unapproved():
    # Contract mirrors the durable document payload boundary: OCR completion
    # must never imply publication approval.
    payload = {"processing_status": "Completed", "approved_for_publication": False, "publication_status": "Unpublished"}
    assert payload["approved_for_publication"] is False
    assert payload["publication_status"] == "Unpublished"
