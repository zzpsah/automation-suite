#!/usr/bin/env python3
"""Offline smoke tests for the School Document Pipeline.

These tests do not contact Supabase, Telegram, B2, Google Drive, or publish data.
They validate deterministic helpers and the evidence-based lifecycle resolver.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROCESSOR_PATH = ROOT / "global-automation" / "scripts" / "document" / "document_processor.py"
RESOLVER_PATH = ROOT / "global-automation" / "scripts" / "document" / "pipeline_state_resolver.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    processor = load_module("document_processor", PROCESSOR_PATH)
    resolver = load_module("pipeline_state_resolver", RESOLVER_PATH)
    checks = []

    if hasattr(processor, "build_display_filename"):
        name = processor.build_display_filename(
            "Spot admission extension letter.pdf",
            "सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में सूचना",
            "बिहार विद्यालय परीक्षा समिति",
            "2026-06-25",
        )
        checks.append(("context_filename", bool(name and name.lower().endswith(".pdf") and len(name) <= 180)))
    else:
        checks.append(("context_filename_helper_present", False))

    checks.append(("checksum_helper_present", any(hasattr(processor, n) for n in ("sha256_file", "file_sha256"))))

    resolver_cases = [
        ("intake", {"id": "1"}, {"id": "i1", "metadata": {}}, "INTAKE_RECEIVED", "storage"),
        ("stored", {"id": "2"}, {"id": "i2", "metadata": {"storage": {"status": "AVAILABLE"}}}, "STORED", "processing"),
        ("processed", {"id": "3", "processing_status": "Completed"}, None, "PROCESSED", "publication"),
        ("publication", {"id": "4", "processing_status": "Completed", "publication_status": "Unpublished"}, None, "PUBLICATION_PENDING", "publication"),
        ("delivery", {"id": "5", "publication_status": "Published", "approved_for_publication": True}, None, "DELIVERY_PENDING", "delivery"),
        ("delivered", {"id": "6", "publication_status": "Published", "approved_for_publication": True, "delivery_status": "Delivered"}, None, "DELIVERED", "none"),
        ("processing_failure", {"id": "7", "processing_status": "Processing Failed"}, None, "RECOVERY_REQUIRED", "processing"),
        ("storage_failure", {"id": "8"}, {"id": "i8", "metadata": {"storage": {"status": "Storage Failed"}}}, "RECOVERY_REQUIRED", "storage"),
        ("unknown", {"id": "9"}, None, "UNKNOWN", "manual_review"),
    ]
    for name, doc, intake, state, action in resolver_cases:
        result = resolver.resolve_state(doc, intake)
        checks.append((f"resolver_{name}", result.state == state and result.next_action == action))

    try:
        resolver.resolve_state({}, None)
        checks.append(("resolver_missing_id_fails_closed", False))
    except ValueError:
        checks.append(("resolver_missing_id_fails_closed", True))

    failed = [name for name, ok in checks if not ok]
    print("=== SCHOOL DOCUMENT PIPELINE OFFLINE SMOKE TEST ===")
    for name, ok in checks:
        print(f"{name}={'PASS' if ok else 'FAIL'}")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
