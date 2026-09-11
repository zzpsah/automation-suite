from global_automation.scripts.document.delivery_reconciliation import build_worklist


def test_unpublished_document_is_ignored():
    docs = [{"id": "d1", "publication_status": "Unpublished", "approved_for_publication": False}]
    assert build_worklist(docs, ["6914456996"], []) == []


def test_sent_recipient_is_not_queued_again():
    docs = [{"id": "d1", "publication_status": "Published", "approved_for_publication": True}]
    audits = [{"document_id": "d1", "operation": "telegram_publication_notification", "details": {"chat_id": "6914456996", "result": "Sent"}}]
    assert build_worklist(docs, ["6914456996"], audits) == []


def test_failed_recipient_remains_recoverable():
    docs = [{"id": "d1", "publication_status": "Published", "approved_for_publication": True}]
    audits = [{"document_id": "d1", "operation": "telegram_publication_notification", "details": {"chat_id": "6914456996", "result": "Failed"}}]
    work = build_worklist(docs, ["6914456996"], audits)
    assert len(work) == 1
    assert work[0].chat_id == "6914456996"
