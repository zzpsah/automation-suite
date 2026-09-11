"""Fail-closed verification for immutable model/runtime artifacts."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
from pathlib import Path
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    version: str
    sha256: str
    size: int | None = None


def _validate(spec: ArtifactSpec) -> None:
    if not spec.name.strip():
        raise ValueError("artifact name is required")
    if not re.fullmatch(r"\d+\.\d+\.\d+", spec.version):
        raise ValueError("artifact version must be immutable MAJOR.MINOR.PATCH")
    if spec.version.lower() == "latest":
        raise ValueError("floating artifact versions are not allowed")
    if not _SHA256.fullmatch(spec.sha256.lower()):
        raise ValueError("artifact sha256 must be 64 hexadecimal characters")
    if spec.size is not None and spec.size < 0:
        raise ValueError("artifact size cannot be negative")


def verify_artifact(path: str | Path, spec: ArtifactSpec) -> bool:
    """Verify existence, optional size and exact SHA-256; fail closed on mismatch."""
    _validate(spec)
    target = Path(path)
    if not target.is_file():
        return False
    data = target.read_bytes()
    if spec.size is not None and len(data) != spec.size:
        return False
    return hashlib.sha256(data).hexdigest() == spec.sha256.lower()


def artifact_to_dict(spec: ArtifactSpec) -> dict:
    _validate(spec)
    return asdict(spec)


__all__ = ["ArtifactSpec", "verify_artifact", "artifact_to_dict"]
