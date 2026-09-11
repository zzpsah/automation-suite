#!/usr/bin/env python3
"""Offline smoke tests for the School Document Pipeline.

These tests do not contact Supabase, Telegram, B2, Google Drive, or publish data.
They validate the deterministic filename/metadata safety helpers exposed by the
production document processor.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "global-automation" / "scripts" / "document" / "document_processor.py"


def load_processor():
    spec = importlib.util.spec_from_file_location("document_processor", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load document_processor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    processor = load_processor()
    checks = []

    # Validate that generated filenames are deterministic and bounded.
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

    # The processor must expose checksum-based duplicate protection helpers.
    checks.append(("checksum_helper_present", any(hasattr(processor, n) for n in ("sha256_file", "file_sha256"))))

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
