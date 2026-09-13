import importlib.util
import os
from pathlib import Path

# The formatter test must remain offline; provide placeholder configuration so
# importing the production module never reaches a real external service.
os.environ.setdefault("SUPABASE_URL", "https://example.invalid")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-only")
os.environ.setdefault("TELEGRAM_OUTPUT_BOT_TOKEN", "test-only")

MODULE = Path(__file__).with_name("telegram_publication_notifier.py")
spec = importlib.util.spec_from_file_location("notifier", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_format_message_contains_core_fields():
    msg = mod.format_message({
        "subject": "सत्र 2026-28 स्पॉट नामांकन",
        "issuing_authority": "बिहार विद्यालय परीक्षा समिति",
        "reference_number": "123",
        "normalized_issue_date": "2026-06-25",
        "received_at": "2026-06-25T10:00:00Z",
        "category": "admission",
        "display_filename": "2026-06-25_BSEB_Spot-Admission.pdf",
        "public_file_url": "https://example.test/file.pdf",
    }, serial_no=1)
    assert "नया सरकारी दस्तावेज़ प्रकाशित" in msg
    assert "स्पॉट नामांकन" in msg
    assert "https://example.test/file.pdf" in msg


def test_recipients_deduplicates_configured_and_source_chats(monkeypatch):
    monkeypatch.setattr(mod, "CONFIGURED_CHAT_IDS", ["100", "200"])
    assert mod.recipients([{"telegram_chat_id": "200"}, {"telegram_chat_id": "300"}]) == ["100", "200", "300"]


def test_missing_public_url_is_not_sent():
    # A missing public URL is not a sendable published artifact.
    assert not {"publication_status": "Published", "approved_for_publication": True, "public_file_url": None}["public_file_url"]
