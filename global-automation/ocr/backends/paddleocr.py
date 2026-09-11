"""Optional PaddleOCR adapter.

PaddleOCR remains an optional dependency: the base OCR package can run with
Tesseract alone. The adapter exposes capability metadata and normalizes the
recognition confidence returned by PaddleOCR to the shared [0, 1] contract.
"""
from __future__ import annotations

from statistics import fmean

from ..backend import OCRResult


class PaddleOCRBackend:
    name = "paddleocr"
    supported_languages = frozenset({"eng", "hin", "hin+eng"})

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PaddleOCR backend is not installed") from exc
        self._engine = PaddleOCR(use_angle_cls=True, lang="hi")

    def extract_image(
        self, image_path: str, *, language: str = "hin+eng", psm: int = 6
    ) -> OCRResult:
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported PaddleOCR language: {language!r}")

        result = self._engine.ocr(image_path, cls=True)
        lines: list[str] = []
        confidences: list[float] = []
        for page in result or []:
            for item in page or []:
                if len(item) < 2 or not item[1]:
                    continue
                text, score = item[1][0], item[1][1] if len(item[1]) > 1 else None
                if str(text).strip():
                    lines.append(str(text))
                try:
                    value = float(score)
                except (TypeError, ValueError):
                    continue
                if 0.0 <= value <= 1.0:
                    confidences.append(value)

        confidence = fmean(confidences) if confidences else None
        return OCRResult(text="\n".join(lines), backend=self.name, confidence=confidence)


__all__ = ["PaddleOCRBackend"]
