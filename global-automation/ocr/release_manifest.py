"""Deterministic release manifest and SHA-256 verification helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ReleaseFile:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class ReleaseManifest:
    product: str
    version: str
    files: tuple[ReleaseFile, ...]


def _validate_version(version: str) -> None:
    parts = version.split(".")
    if len(parts) != 3 or any(not p.isdigit() for p in parts):
        raise ValueError("version must be semantic MAJOR.MINOR.PATCH")


def _file_record(root: Path, path: Path) -> ReleaseFile:
    data = path.read_bytes()
    return ReleaseFile(path.as_posix(), hashlib.sha256(data).hexdigest(), len(data))


def build_release_manifest(root: str | Path, version: str, paths: Iterable[str | Path]) -> ReleaseManifest:
    """Hash selected release files in stable path order; never hash the manifest itself."""
    _validate_version(version)
    base = Path(root).resolve()
    records: list[ReleaseFile] = []
    for raw in paths:
        path = (base / raw).resolve()
        try:
            relative = path.relative_to(base)
        except ValueError as exc:
            raise ValueError("release path must stay inside root") from exc
        if not path.is_file():
            raise FileNotFoundError(str(relative))
        records.append(_file_record(base, path))
    records.sort(key=lambda item: item.path)
    return ReleaseManifest("Government Document Vision & OCR Platform", version, tuple(records))


def manifest_to_dict(manifest: ReleaseManifest) -> dict:
    return {"product": manifest.product, "version": manifest.version,
            "files": [asdict(item) for item in manifest.files]}


def manifest_to_json(manifest: ReleaseManifest) -> str:
    return json.dumps(manifest_to_dict(manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def verify_release_manifest(root: str | Path, manifest: ReleaseManifest) -> tuple[bool, tuple[str, ...]]:
    """Verify every recorded file exists and has the exact recorded digest/size."""
    base = Path(root).resolve()
    errors: list[str] = []
    for item in manifest.files:
        path = (base / item.path).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            errors.append(f"outside_root:{item.path}")
            continue
        if not path.is_file():
            errors.append(f"missing:{item.path}")
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != item.size:
            errors.append(f"size_mismatch:{item.path}")
        if digest != item.sha256:
            errors.append(f"sha256_mismatch:{item.path}")
    return not errors, tuple(errors)


__all__ = ["ReleaseFile", "ReleaseManifest", "build_release_manifest", "manifest_to_dict", "manifest_to_json", "verify_release_manifest"]
