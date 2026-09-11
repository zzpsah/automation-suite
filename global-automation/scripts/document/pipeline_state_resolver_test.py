#!/usr/bin/env python3
"""Offline tests for the evidence-based lifecycle resolver."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "global-automation" / "scripts" / "document" / "pipeline_state_resolver.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pipeline_state_resolver", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load resolver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    r = load_module()
    checks = []

    def state(doc, intake=None):
        return r.resolve_state(doc, intake).state

    checks.append(("failed_processing", state({"id": "1", "processing_status": "Processing Failed"}) == "RECOVERY_REQUIRED"))
    checks.append(("stored", state({"id": "2"}, {"metadata": {"storage": {"status": "AVAILABLE"}}}) == "STORED"))
    checks.append(("processed", state({"id": "3", "processing_status": "Completed"}) == "PROCESSED"))
    checks.append(("publication_pending", state({"id": "4", "processing_status": "Completed", "publication_status": "Unpublished"}) == "PUBLICATION_PENDING"))
    checks.append(("delivery_pending", state({"id": "5", "publication_status": "Published", "approved_for_publication": True}) == "DELIVERY_PENDING"))
    checks.append(("delivered", state({"id": "6", "publication_status": "Published", "approved_for_publication": True, "delivery_status": "Sent"}) == "DELIVERED"))
    checks.append(("no_publication_guess", r.resolve_state({"id": "7", "processing_status": "Completed", "publication_status": "Unpublished"}).next_action == "publication"))

    failed = [name for name, ok in checks if not ok]
    print("=== PIPELINE STATE RESOLVER TEST ===")
    for name, ok in checks:
        print(f"{name}={'PASS' if ok else 'FAIL'}")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
