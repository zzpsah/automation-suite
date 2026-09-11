"""Advanced, reusable image preprocessing for OCR.

The preprocessing layer never mutates source files. It creates deterministic
working variants so the OCR engine can select the best evidence-preserving
representation for a page.
"""
from .image import ImageProfile, analyze_image, prepare_variants

__all__ = ["ImageProfile", "analyze_image", "prepare_variants"]
