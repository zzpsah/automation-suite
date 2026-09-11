"""Safe local backup/restore helpers for the SQLite search store."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import sqlite3
import tempfile


def backup_sqlite(source: str | Path, destination: str | Path) -> str:
    """Create a consistent SQLite backup and return its SHA-256 digest."""
    src = Path(source)
    dst = Path(destination)
    if not src.is_file():
        raise FileNotFoundError(str(src))
    if src.resolve() == dst.resolve():
        raise ValueError("destination must differ from source")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(src) as source_db, sqlite3.connect(dst) as target_db:
        source_db.backup(target_db)
    with dst.open("rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def verify_sqlite(path: str | Path) -> bool:
    """Verify SQLite integrity using SQLite's own integrity_check."""
    with sqlite3.connect(path) as db:
        row = db.execute("PRAGMA integrity_check").fetchone()
    return bool(row and row[0] == "ok")


def restore_sqlite(backup: str | Path, destination: str | Path) -> str:
    """Restore a verified SQLite backup atomically and return its SHA-256 digest."""
    src = Path(backup)
    dst = Path(destination)
    if not src.is_file():
        raise FileNotFoundError(str(src))
    if not verify_sqlite(src):
        raise ValueError("backup failed SQLite integrity_check")
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{dst.name}.", suffix=".restore", dir=dst.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with sqlite3.connect(src) as source_db, sqlite3.connect(temp) as target_db:
            source_db.backup(target_db)
        if not verify_sqlite(temp):
            raise ValueError("restored database failed SQLite integrity_check")
        os.replace(temp, dst)
    finally:
        temp.unlink(missing_ok=True)
    with dst.open("rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


__all__ = ["backup_sqlite", "verify_sqlite", "restore_sqlite"]
