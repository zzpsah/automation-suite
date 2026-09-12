#!/usr/bin/env python3
"""Deterministic verification loop for the School Document Pipeline.

This is intentionally offline: it never contacts Supabase, B2, Drive, Telegram,
or the publication layer. Production storage failures must be investigated
separately rather than hidden by this verification loop.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

CHECKS = [
    ("compile_document_pipeline", [sys.executable, "-m", "compileall", "-q", "global-automation/scripts/document"]),
    ("compile_govdoc_ocr", [sys.executable, "-m", "compileall", "-q", "global-automation/govdoc-ocr"]),
    ("govdoc_tests", [sys.executable, "-m", "pytest", "-q", "global-automation/govdoc-ocr/tests"]),
    ("govdoc_smoke", [sys.executable, "global-automation/govdoc-ocr/smoke_test.py"]),
    ("pipeline_offline_smoke", [sys.executable, "global-automation/scripts/document/pipeline_smoke_test.py"]),
]


def run(name: str, command: list[str]) -> bool:
    print(f"\n=== {name} ===")
    result = subprocess.run(command, cwd=ROOT)
    ok = result.returncode == 0
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    failed = [name for name, command in CHECKS if not run(name, command)]
    print("\n=== SCHOOL DOCUMENT PIPELINE VERIFICATION ===")
    if failed:
        print("FAILED:", ", ".join(failed))
        print("Production B2/Supabase state was not changed or repaired by this check.")
        return 1
    print("ALL OFFLINE CHECKS PASSED")
    print("NOTE: this does not prove production B2/Supabase connectivity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
