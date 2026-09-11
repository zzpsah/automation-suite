#!/usr/bin/env python3
"""Offline dry-run for Telegram publication notifications.

No Telegram or Supabase writes. Uses a local fixture (or stdin JSON) and prints
exact recipient resolution plus the formatted message that production would send.
"""
import json
import os
import sys

from telegram_publication_notifier import format_message, recipients


def main():
    configured = os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS", "")
    fixture = {
        "id": "DRY-RUN-DOCUMENT",
        "original_filename": "Spot admission extension letter.pdf",
        "display_filename": "2026-06-25_BSEB_Spot-Admission_Inter-Date-Extension.pdf",
        "subject": "सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में सूचना",
        "issuing_authority": "बिहार विद्यालय परीक्षा समिति",
        "reference_number": "DRY-RUN/2026",
        "normalized_issue_date": "2026-06-25",
        "category": "admission",
        "public_file_url": "https://example.invalid/public-document.pdf",
    }
    intake = [{"telegram_chat_id": "dry-run-origin-chat"}]
    targets = [x.strip() for x in configured.split(",") if x.strip()]
    targets = list(dict.fromkeys(targets + recipients(intake)))
    print("DRY RUN — NO TELEGRAM API CALLS, NO DATABASE WRITES")
    print("Recipients:")
    for target in targets:
        print(f"- {target}")
    print("\nFormatted message:\n")
    print(format_message(fixture))
    print("\nPDF action: sendDocument(public_file_url) — simulated only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
