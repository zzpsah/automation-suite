"""Evidence-preserving extractive summary."""
from __future__ import annotations
import re


def summarize(text: str, max_chars: int = 600) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    summary = " ".join(lines[:5])
    return summary[:max_chars].rstrip() + ("…" if len(summary) > max_chars else "")
