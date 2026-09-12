"""Stable import alias for the hyphenated GovDOC OCR source directory.

The canonical source remains ``global-automation/govdoc-ocr`` for backward
compatibility. This package only provides the Python import name
``govdoc_ocr``; it does not duplicate implementation files.
"""
from pathlib import Path

# Point Python's submodule loader at the canonical hyphenated source tree.
__path__ = [str(Path(__file__).resolve().parent.parent / "govdoc-ocr")]

from .ocr_service import process_document, process_image, process_pdf, process_pdf_bytes
from .regions import OCRRegion, normalize_region, regions_to_dict
from .layout import order_reading, rows, table_candidates
from .reading_order import reading_order, reading_lines, line_text
from .backend_policy import BackendDecision, choose_backend
from .regression import RegressionCase, load_corpus, save_case, exact_match
from .benchmarks import cer, wer, benchmark

__all__ = [
    "process_document", "process_image", "process_pdf", "process_pdf_bytes",
    "OCRRegion", "normalize_region", "regions_to_dict",
    "order_reading", "rows", "table_candidates",
    "reading_order", "reading_lines", "line_text",
    "BackendDecision", "choose_backend",
    "RegressionCase", "load_corpus", "save_case", "exact_match",
    "cer", "wer", "benchmark",
]
