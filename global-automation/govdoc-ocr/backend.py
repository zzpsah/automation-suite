"""Pluggable OCR backend contract for GovDOC OCR/Vision."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

from .regions import OCRRegion

@dataclass(frozen=True)
class OCRResult:
    text: str
    backend: str
    confidence: float | None = None
    regions: tuple[OCRRegion, ...] = ()

class OCRBackend(Protocol):
    name: str
    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult: ...

class TesseractBackend:
    name = "tesseract"
    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        import subprocess
        result = subprocess.run(["tesseract", image_path, "stdout", "-l", language, "--psm", str(psm)], check=True, capture_output=True, text=True, encoding="utf-8")
        regions = _tesseract_regions(image_path, language, psm)
        return OCRResult(result.stdout, self.name, _mean_confidence(regions), tuple(regions))

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
        regions = []
        index = 0
        for page in result or []:
            for item in page or []:
                if len(item) < 2 or not item[1]:
                    continue
                text = str(item[1][0])
                lines.append(text)
                confidence = None
                if len(item[1]) > 1:
                    try:
                        confidence = float(item[1][1])
                        scores.append(confidence)
                    except (TypeError, ValueError):
                        pass
                try:
                    points = item[0]
                    xs = [float(point[0]) for point in points]
                    ys = [float(point[1]) for point in points]
                    if len(xs) >= 2 and len(ys) >= 2:
                        index += 1
                        regions.append(OCRRegion(f"region-{index}", (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))), text, confidence, source=self.name))
                except (TypeError, ValueError, IndexError):
                    pass
        return OCRResult("\n".join(lines), self.name, sum(scores)/len(scores) if scores else None, tuple(regions))

def _tesseract_regions(image_path: str, language: str, psm: int) -> list[OCRRegion]:
    try:
        import pytesseract
        from pytesseract import Output
        data = pytesseract.image_to_data(image_path, lang=language, config=f"--psm {psm}", output_type=Output.DICT)
    except (ImportError, RuntimeError, OSError):
        return []
    regions = []
    index = 0
    for i, text in enumerate(data.get("text", [])):
        text = str(text or "").strip()
        try:
            confidence = float(data.get("conf", [""])[i])
        except (TypeError, ValueError, IndexError):
            confidence = None
        if not text or confidence is None or confidence < 0:
            continue
        try:
            x, y = int(data["left"][i]), int(data["top"][i])
            w, h = int(data["width"][i]), int(data["height"][i])
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        index += 1
        regions.append(OCRRegion(f"region-{index}", (x, y, x + w, y + h), text, confidence / 100.0, source="tesseract"))
    return regions

def _mean_confidence(regions: list[OCRRegion]) -> float | None:
    values = [r.confidence for r in regions if r.confidence is not None]
    return sum(values) / len(values) if values else None

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
