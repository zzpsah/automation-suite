from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_event(path: Path, action: str, **details: Any) -> None:
    """Append non-secret operational audit metadata as JSONL.

    Callers must not pass credentials, session tokens, OTP/CAPTCHA values, or
    unnecessary student PII.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        **details,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
