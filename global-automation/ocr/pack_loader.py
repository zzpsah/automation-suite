"""Safe loader for versioned OCR language packs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parent / "language_packs"


def load_pack(name: str, root: Path | None = None) -> dict[str, Any]:
    """Load a JSON language pack without modifying it."""
    safe_name = Path(name).name
    if safe_name != name or not safe_name.endswith(".json"):
        safe_name += ".json"
    path = (root or PACK_ROOT) / safe_name
    if not path.is_file():
        raise FileNotFoundError(f"Language pack not found: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Language pack must be a JSON object")
    if not data.get("name") or not data.get("version"):
        raise ValueError("Language pack requires name and version")
    return data


def list_packs(root: Path | None = None) -> list[str]:
    return sorted(p.stem for p in (root or PACK_ROOT).glob("*.json"))
