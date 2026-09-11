"""Reusable OCR engine for Hindi/English government documents."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .correction import correct_ocr_text
from .preprocessing.image import analyze_image, prepare_variants
from .preprocessing.quality import score_text


def extract_embedded_pdf_pages(pdf_path: str) -> list[str]:
    """Extract embedded text page-by-page without OCR."""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    return [correct_ocr_text(page.extract_text() or "") for page in reader.pages]


def extract_embedded_pdf_text(pdf_path: str) -> str:
    return "\n\n".join(extract_embedded_pdf_pages(pdf_path))


def tesseract_available() -> bool:
    try:
        subprocess.run(["tesseract", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _run_tesseract(image_path: str, *, lang: str, psm: int) -> str:
    result = subprocess.run(
        ["tesseract", image_path, "stdout", "-l", lang, "--psm", str(psm)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return correct_ocr_text(result.stdout)


def ocr_image_detailed(image_path: str, lang: str = "hin+eng", psm: int = 6, *, strategy: str = "auto") -> dict[str, Any]:
    """OCR an image through multiple safe preprocessing candidates."""
    if not Path(image_path).exists():
        raise FileNotFoundError(image_path)
    if not tesseract_available():
        raise RuntimeError("Tesseract is not installed or unavailable")
    image_quality = analyze_image(image_path)
    with tempfile.TemporaryDirectory(prefix="global-ocr-") as temp_dir:
        candidates = prepare_variants(image_path, temp_dir, strategy=strategy)
        results = []
        baseline = _run_tesseract(image_path, lang=lang, psm=psm)
        results.append((score_text(baseline), "original", baseline))
        for candidate in candidates:
            text = _run_tesseract(candidate, lang=lang, psm=psm)
            results.append((score_text(text), Path(candidate).stem, text))
        score, selected, text = max(results, key=lambda item: (item[0], -len(item[1])))
    return {"text": text, "backend": "tesseract", "language": lang, "psm": psm,
            "selected_variant": selected, "selection_score": score,
            "image_quality": image_quality, "candidate_count": len(results)}


def ocr_image(image_path: str, lang: str = "hin+eng", psm: int = 6) -> str:
    return ocr_image_detailed(image_path, lang=lang, psm=psm)["text"]


def render_pdf(pdf_path: str, output_dir: str, dpi: int = 250) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / "page"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-jpeg", pdf_path, str(prefix)], check=True, capture_output=True, text=True)
    return [str(p) for p in sorted(out.glob("page-*.jpg"))]


def extract_document_pages(pdf_path: str, work_dir: str, min_embedded_chars: int = 80) -> tuple[list[str], str]:
    """Return ordered page text and extraction method."""
    pages = extract_embedded_pdf_pages(pdf_path)
    if len("".join("".join(page.split()) for page in pages)) >= min_embedded_chars:
        return pages, "embedded-text"
    rendered = render_pdf(pdf_path, work_dir)
    return [ocr_image(page) for page in rendered], "tesseract-hin+eng-quality-aware"


def extract_document_text(pdf_path: str, work_dir: str, min_embedded_chars: int = 80) -> tuple[str, str]:
    pages, method = extract_document_pages(pdf_path, work_dir, min_embedded_chars=min_embedded_chars)
    return correct_ocr_text("\n\n".join(pages)), method
