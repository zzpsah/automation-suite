#!/usr/bin/env python3
"""Evidence-based document lifecycle state resolver.

The resolver is deliberately side-effect free. It converts observed pipeline
evidence into one authoritative stage and a safe next action. Workers remain
responsible for mutations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LifecycleState:
    document_id: str
    state: str
    next_action: str
    reason: str
    manual: bool = False


def resolve_state(doc: dict[str, Any], intake: dict[str, Any] | None = None) -> LifecycleState:
    did = str(doc.get("id") or "")
    if not did:
        raise ValueError("document id is required")
    intake = intake or {}
    metadata = intake.get("metadata") or {}
    storage = metadata.get("storage") or {}
    storage_state = str(storage.get("status") or intake.get("storage_status") or "")
    processing = str(doc.get("processing_status") or "")
    publication = str(doc.get("publication_status") or "")
    approved = doc.get("approved_for_publication") is True
    delivery = str(doc.get("delivery_status") or "")

    if processing in {"Processing Failed", "Needs Manual Review", "Action Required"}:
        return LifecycleState(did, "RECOVERY_REQUIRED", "processing", f"processing_state={processing}", True)
    if storage_state in {"Processing Failed", "Storage Failed", "Failed", "Error"}:
        return LifecycleState(did, "RECOVERY_REQUIRED", "storage", f"storage_state={storage_state}")
    if publication == "Published" and approved and delivery in {"Sent", "Delivered"}:
        return LifecycleState(did, "DELIVERED", "none", "published_and_delivery_confirmed")
    if publication == "Published" and approved:
        return LifecycleState(did, "DELIVERY_PENDING", "delivery", "published_and_approved")
    if publication == "Unpublished" and processing == "Completed":
        # Eligibility belongs to the publication worker; resolver must not guess.
        return LifecycleState(did, "PUBLICATION_PENDING", "publication", "processing_complete_but_publication_not_confirmed")
    if processing == "Completed":
        return LifecycleState(did, "PROCESSED", "publication", "processing_complete")
    if storage_state in {"AVAILABLE", "Stored"}:
        return LifecycleState(did, "STORED", "processing", "storage_confirmed")
    if intake:
        return LifecycleState(did, "INTAKE_RECEIVED", "storage", "intake_exists_but_storage_not_confirmed")
    return LifecycleState(did, "UNKNOWN", "manual_review", "insufficient_evidence", True)
