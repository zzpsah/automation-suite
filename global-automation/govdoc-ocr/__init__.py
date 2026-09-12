"""GovDOC OCR Engine / GovDOC Vision public package."""
from .ocr_service import process_document, process_image, process_pdf, process_pdf_bytes
from .regions import OCRRegion, normalize_region, regions_to_dict
from .backend_policy import BackendDecision, choose_backend
from .regression import RegressionCase, load_corpus, save_case, exact_match
from .benchmarks import cer, wer, benchmark

__all__=[
    "process_document","process_image","process_pdf","process_pdf_bytes",
    "OCRRegion","normalize_region","regions_to_dict",
    "BackendDecision","choose_backend",
    "RegressionCase","load_corpus","save_case","exact_match",
    "cer","wer","benchmark",
]
