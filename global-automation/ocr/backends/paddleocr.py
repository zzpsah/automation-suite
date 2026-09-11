"""Optional PaddleOCR adapter.

PaddleOCR is deliberately not imported by the base package. This adapter is
an extension point; enabling it requires a pinned dependency/model artifact
and shared backend tests/benchmarks to pass.
"""
from ..backend import OCRBackend, OCRResult


class PaddleOCRBackend:
    name = "paddleocr"

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PaddleOCR backend is not installed") from exc
        self._engine = PaddleOCR(use_angle_cls=True, lang="hi")

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        result = self._engine.ocr(image_path, cls=True)
        lines = []
        for page in result or []:
            for item in page or []:
                if len(item) >= 2 and item[1]:
                    lines.append(str(item[1][0]))
        return OCRResult(text="\n".join(lines), backend=self.name)

__all__ = ["PaddleOCRBackend"]
