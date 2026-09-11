"""Stable, machine-readable error taxonomy for OCR platform consumers."""
from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_FORMAT = "unsupported_format"
    OCR_BACKEND_UNAVAILABLE = "ocr_backend_unavailable"
    OCR_BACKEND_FAILURE = "ocr_backend_failure"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    STORAGE_FAILURE = "storage_failure"
    RESOURCE_LIMIT = "resource_limit"
    CONFIGURATION_ERROR = "configuration_error"
    RELEASE_INTEGRITY_FAILURE = "release_integrity_failure"
    INTERNAL_ERROR = "internal_error"


class OCRPlatformError(Exception):
    """Base exception carrying a stable code and safe public detail."""
    code = ErrorCode.INTERNAL_ERROR

    def __init__(self, detail: str, *, operation: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.operation = operation

    def to_dict(self) -> dict:
        return {"code": self.code.value, "detail": self.detail, "operation": self.operation}


class InvalidInputError(OCRPlatformError):
    code = ErrorCode.INVALID_INPUT


class BackendUnavailableError(OCRPlatformError):
    code = ErrorCode.OCR_BACKEND_UNAVAILABLE


class StorageError(OCRPlatformError):
    code = ErrorCode.STORAGE_FAILURE


__all__ = ["ErrorCode", "OCRPlatformError", "InvalidInputError", "BackendUnavailableError", "StorageError"]
