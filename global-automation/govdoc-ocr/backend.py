"""Pluggable OCR backend contract for GovDOC OCR/Vision."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class OCRResult:
    text: str
    backend: str
    confidence: float | None = None

class OCRBackend(Protocol):
    name: str
    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult: ...

class TesseractBackend:
    name = "tesseract"
    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        import subprocess
        result = subprocess.run(["tesseract", image_path, "stdout", "-l", language, "--psm", str(psm)], check=True, capture_output=True, text=True, encoding="utf-8")
        return OCRResult(result.stdout, self.name)

class PaddleOCRBackend:
    name = "paddleocr"
    def __init__(self):
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError("PaddleOCR is optional; install the paddle extra to enable it") from exc
        self._engine = PaddleOCR(use_angle_cls=True, lang="hi")
    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        result = self._engine.ocr(image_path, cls=True)
        lines = []
        scores = []
        for page in result or []:
            for item in page or []:
                if len(item) >= 2 and item[1]:
                    lines.append(str(item[1][0]))
                    if len(item[1]) > 1:
                        try: scores.append(float(item[1][1]))
                        except (TypeError, ValueError): pass
        return OCRResult("\n".join(lines), self.name, sum(scores)/len(scores) if scores else None)

def get_backend(name: str = "tesseract") -> OCRBackend:
    if name == "tesseract": return TesseractBackend()
    if name == "paddleocr": return PaddleOCRBackend()
    raise ValueError(f"Unsupported OCR backend: {name}")


def available_backends() -> list[str]:
    names = ["tesseract"]
    try:
        import paddleocr  # noqa: F401
        names.append("paddleocr")
    except ImportError:
        pass
    return names
