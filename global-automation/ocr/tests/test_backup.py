from pathlib import Path

from ocr.backup import backup_sqlite, restore_sqlite, verify_sqlite
from ocr.persistent_search import SQLiteSearchStore
from ocr.search_index import SearchDocument, SearchEntity


def test_sqlite_backup_restore(tmp_path: Path) -> None:
    source = tmp_path / "search.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    store = SQLiteSearchStore(str(source))
    store.upsert_many(
        [SearchDocument("doc-1", 1, "b-1", "पत्रांक REF-1")],
        [SearchEntity("doc-1", "e-1", "reference", "REF-1", 1, "b-1", 0.98)],
    )
    store.close()
    assert verify_sqlite(source)
    digest = backup_sqlite(source, backup)
    assert len(digest) == 64
    restored_digest = restore_sqlite(backup, restored)
    assert restored_digest == __import__("hashlib").sha256(restored.read_bytes()).hexdigest()
    restored_store = SQLiteSearchStore(str(restored))
    hits = restored_store.search("REF-1")
    restored_store.close()
    assert hits and hits[0].document_id == "doc-1"
