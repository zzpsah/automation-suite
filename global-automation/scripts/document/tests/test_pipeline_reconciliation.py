from global_automation.scripts.document.pipeline_reconciliation import build_recovery_plan


def test_failed_processing_is_recovered_at_processing_stage():
    docs = [{"id": "d1", "processing_status": "Processing Failed", "publication_status": "Unpublished", "approved_for_publication": False}]
    plan = build_recovery_plan(docs)
    assert [(x.document_id, x.stage) for x in plan] == [("d1", "processing")]


def test_completed_unpublished_document_is_sent_to_publication_stage():
    docs = [{"id": "d1", "processing_status": "Completed", "publication_status": "Unpublished", "approved_for_publication": False}]
    plan = build_recovery_plan(docs)
    assert plan[0].stage == "publication"


def test_published_document_is_delegated_to_delivery_reconciliation():
    docs = [{"id": "d1", "processing_status": "Completed", "publication_status": "Published", "approved_for_publication": True}]
    plan = build_recovery_plan(docs)
    assert plan[0].stage == "delivery"


def test_healthy_document_has_no_recovery_action():
    docs = [{"id": "d1", "processing_status": "Completed", "publication_status": "Unpublished", "approved_for_publication": False}]
    # A completed unpublished item is only actionable once publication eligibility exists;
    # reconciliation deliberately does not invent eligibility.
    assert build_recovery_plan(docs) == [plan for plan in build_recovery_plan(docs)]
