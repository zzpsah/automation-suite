"""Global Sarkari OCR package."""

from .ocr_engine import extract_document_text, extract_embedded_pdf_text, ocr_image, ocr_image_detailed, render_pdf
from .ocr_service import process_file, process_image, process_pdf
from .sarkari_normalizer import SarkariMetadata, extract_metadata, normalize_sarkari_text
from .backend_policy import choose_backend, choose_from_benchmarks

__all__ = [
    "extract_document_text",
    "extract_embedded_pdf_text",
    "ocr_image",
    "ocr_image_detailed",
    "render_pdf",
    "process_file",
    "process_image",
    "process_pdf",
    "SarkariMetadata",
    "extract_metadata",
    "normalize_sarkari_text",
    "choose_backend",
    "choose_from_benchmarks",
]
