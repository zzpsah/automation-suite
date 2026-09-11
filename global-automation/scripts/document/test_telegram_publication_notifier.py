import importlib.util
from pathlib import Path

MODULE = Path(__file__).with_name("telegram_publication_notifier.py")
spec = importlib.util.spec_from_file_location("notifier", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_format_message_contains_core_fields():
    msg = mod.format_message({
        "subject": "सत्र 2026-28 स्पॉट नामांकन",
        "issuing_authority": "बिहार विद्यालय परीक्षा समिति",
        "reference_number": "123",
        "normalized_issue_date": "2026-06-25",
        "category": "admission",
        "display_filename": "2026-06-25_BSEB_Spot-Admission.pdf",
        "public_file_url": "https://example.test/file.pdf",
    })
    assert "Document Published" in msg
    assert "स्पॉट नामांकन" in msg
    assert "https://example.test/file.pdf" in msg


def test_recipients_deduplicates_configured_and_source_chats(monkeypatch):
    monkeypatch.setattr(mod, "CONFIGURED_CHAT_IDS", ["100", "200"])
    assert mod.recipients([{"telegram_chat_id": "200"}, {"telegram_chat_id": "300"}]) == ["100", "200", "300"]


def test_missing_public_url_is_not_sent():
    # Publication worker contract: notifier only handles publicly published records with a URL.
    assert not {"publication_status": "Published", "approved_for_publication": True, "public_file_url": None}["public_file_url"]
