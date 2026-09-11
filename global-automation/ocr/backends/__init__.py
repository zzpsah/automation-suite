"""Controlled OCR backend adapters."""
from .tesseract import TesseractBackend
from .paddleocr import PaddleOCRBackend
from .vlm import VLMBackend

__all__ = ["TesseractBackend", "PaddleOCRBackend", "VLMBackend"]
