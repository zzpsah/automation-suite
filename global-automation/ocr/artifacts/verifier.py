"""Deterministic verification for controlled OCR artifacts."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(path: str | Path, expected_sha256: str, expected_size: int | None = None) -> bool:
    file_path = Path(path)
    if expected_size is not None and file_path.stat().st_size != expected_size:
        return False
    return sha256_file(file_path).casefold() == expected_sha256.casefold()


def require_pinned_artifact(metadata: Mapping[str, object]) -> None:
    version = str(metadata.get("version", "")).strip()
    checksum = str(metadata.get("sha256", "")).strip()
    if not version or version.lower() == "latest":
        raise ValueError("Production OCR artifacts require an explicit version")
    if len(checksum) != 64:
        raise ValueError("Production OCR artifacts require a SHA-256 checksum")

__all__ = ["sha256_file", "verify_artifact", "require_pinned_artifact"]
