#!/usr/bin/env python3
"""Deterministic offline verification loop for the School Document Pipeline."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH = os.pathsep.join([
    str(ROOT / "global-automation"),
    str(ROOT / "global-automation" / "govdoc-ocr"),
    os.environ.get("PYTHONPATH", ""),
]).strip(os.pathsep)

CHECKS = [
    ("compile_document_pipeline", [sys.executable, "-m", "compileall", "-q", "global-automation/scripts/document"]),
    ("compile_govdoc_ocr", [sys.executable, "-m", "compileall", "-q", "global-automation/govdoc-ocr"]),
    ("compile_govdoc_ocr_alias", [sys.executable, "-m", "compileall", "-q", "global-automation/govdoc_ocr"]),
    ("govdoc_tests", [sys.executable, "-m", "pytest", "-q", "global-automation/govdoc-ocr/tests"]),
    ("adapter_contract_tests", [sys.executable, "-m", "pytest", "-q", "global-automation/scripts/document/test_govdoc_ocr_adapter.py"]),
    ("resilience_contract_tests", [sys.executable, "-m", "pytest", "-q", "global-automation/scripts/document/test_govdoc_resilience.py"]),
    ("govdoc_smoke", [sys.executable, "global-automation/govdoc-ocr/smoke_test.py"]),
    ("pipeline_offline_smoke", [sys.executable, "global-automation/scripts/document/pipeline_smoke_test.py"]),
]


def run(name: str, command: list[str], completed: int, total: int) -> bool:
    percent = int(completed * 100 / total)
    print(f"\n[{percent}%] START {name}", flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH
    result = subprocess.run(command, cwd=ROOT, env=env)
    ok = result.returncode == 0
    next_percent = int((completed + 1) * 100 / total)
    print(f"[{next_percent}%] {name}={'PASS' if ok else 'FAIL'}", flush=True)
    return ok


def main() -> int:
    total = len(CHECKS)
    failed = []
    for index, (name, command) in enumerate(CHECKS):
        if not run(name, command, index, total):
            failed.append(name)

    print("\n=== SCHOOL DOCUMENT PIPELINE VERIFICATION ===")
    if failed:
        print("FAILED:", ", ".join(failed))
        print("Progress reached", int((total - len(failed)) * 100 / total), "% of checks passing.")
        print("Production B2/Supabase state was not changed or repaired by this check.")
        return 1
    print("ALL OFFLINE CHECKS PASSED")
    print("Progress: 100%")
    print("NOTE: this does not prove production B2/Supabase connectivity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
