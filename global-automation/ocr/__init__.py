"""Global Sarkari OCR package."""

from .release_manifest import ReleaseFile, ReleaseManifest, build_release_manifest, manifest_to_dict, manifest_to_json, verify_release_manifest
from .errors import ErrorCode, OCRPlatformError, InvalidInputError, BackendUnavailableError, StorageError
from .observability import OperationEvent, emit_event, event_to_json
from .backup import backup_sqlite, verify_sqlite, restore_sqlite

__all__ = ["ReleaseFile", "ReleaseManifest", "build_release_manifest", "manifest_to_dict", "manifest_to_json", "verify_release_manifest", "ErrorCode", "OCRPlatformError", "InvalidInputError", "BackendUnavailableError", "StorageError", "OperationEvent", "emit_event", "event_to_json", "backup_sqlite", "verify_sqlite", "restore_sqlite"]
