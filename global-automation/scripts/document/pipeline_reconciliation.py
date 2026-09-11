#!/usr/bin/env python3
"""Deterministic lifecycle reconciliation for the document pipeline.

This module only classifies work; workers remain responsible for side effects.
It is safe to run repeatedly and keeps storage/processing/publication/delivery
responsibilities separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryAction:
    document_id: str
    stage: str
    reason: str


def classify_document(doc: dict[str, Any], intake: dict[str, Any] | None = None) -> RecoveryAction | None:
    did = str(doc.get("id") or "")
    if not did:
        return None
    publication = str(doc.get("publication_status") or "")
    processing = str(doc.get("processing_status") or "")
    approved = doc.get("approved_for_publication") is True
    storage = (intake or {}).get("metadata") or {}
    storage_state = (storage.get("storage") or {}).get("status") or (intake or {}).get("storage_status") or ""

    if processing in {"Processing Failed", "Needs Manual Review", "Action Required"}:
        return RecoveryAction(did, "processing", f"processing_state={processing}")
    if storage_state in {"Processing Failed", "Failed", "Error"}:
        return RecoveryAction(did, "storage", f"storage_state={storage_state}")
    if publication == "Unpublished" and processing == "Completed" and approved is False:
        return RecoveryAction(did, "publication", "completed_document_not_published")
    if publication == "Published" and approved:
        # Delivery reconciliation owns the final delivery decision.
        return RecoveryAction(did, "delivery", "published_document_requires_delivery_reconciliation")
    return None


def build_recovery_plan(documents: list[dict[str, Any]], intakes: dict[str, dict[str, Any]] | None = None) -> list[RecoveryAction]:
    intakes = intakes or {}
    actions: list[RecoveryAction] = []
    for doc in documents:
        action = classify_document(doc, intakes.get(str(doc.get("id"))))
        if action:
            actions.append(action)
    return actions
