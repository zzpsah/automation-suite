"""Stable core facade for consumers and future integrations."""
from ..ocr_service import OCR_SERVICE_VERSION, process_file, process_image, process_pdf
from ..backend import OCRBackend, OCRResult, get_backend

__all__ = [
    "OCR_SERVICE_VERSION",
    "process_file",
    "process_image",
    "process_pdf",
    "OCRBackend",
    "OCRResult",
    "get_backend",
]
