"""Reusable OCR engine for Hindi/English government documents."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .correction import correct_ocr_text
from .preprocessing.image import analyze_image, prepare_variants
from .preprocessing.quality import score_text


def extract_embedded_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF without OCR when useful."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    return correct_ocr_text("\n".join(page.extract_text() or "" for page in reader.pages))


def tesseract_available() -> bool:
    try:
        subprocess.run(["tesseract", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _run_tesseract(image_path: str, *, lang: str, psm: int) -> str:
    result = subprocess.run(
        ["tesseract", image_path, "stdout", "-l", lang, "--psm", str(psm)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return correct_ocr_text(result.stdout)


def ocr_image_detailed(
    image_path: str,
    lang: str = "hin+eng",
    psm: int = 6,
    *,
    strategy: str = "auto",
) -> dict[str, Any]:
    """OCR an image through multiple safe preprocessing candidates.

    The original image is never changed. Candidate selection is deterministic
    and based only on output-quality heuristics; benchmark ground truth remains
    the authority for accuracy claims.
    """
    if not Path(image_path).exists():
        raise FileNotFoundError(image_path)
    if not tesseract_available():
        raise RuntimeError("Tesseract is not installed or unavailable")

    image_quality = analyze_image(image_path)
    with tempfile.TemporaryDirectory(prefix="global-ocr-") as temp_dir:
        candidates = prepare_variants(image_path, temp_dir, strategy=strategy)
        results = []
        # Keep the raw/original representation as a baseline when requested.
        baseline = _run_tesseract(image_path, lang=lang, psm=psm)
        results.append((score_text(baseline), "original", baseline))
        for candidate in candidates:
            text = _run_tesseract(candidate, lang=lang, psm=psm)
            results.append((score_text(text), Path(candidate).stem, text))
        score, selected, text = max(results, key=lambda item: (item[0], -len(item[1])))

    return {
        "text": text,
        "backend": "tesseract",
        "language": lang,
        "psm": psm,
        "selected_variant": selected,
        "selection_score": score,
        "image_quality": image_quality,
        "candidate_count": len(results),
    }


def ocr_image(image_path: str, lang: str = "hin+eng", psm: int = 6) -> str:
    """Run quality-aware Tesseract OCR and return corrected text."""
    return ocr_image_detailed(image_path, lang=lang, psm=psm)["text"]


def render_pdf(pdf_path: str, output_dir: str, dpi: int = 250) -> list[str]:
    """Render PDF pages to JPEG files using pdftoppm."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / "page"
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-jpeg", pdf_path, str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [str(p) for p in sorted(out.glob("page-*.jpg"))]


def extract_document_text(pdf_path: str, work_dir: str, min_embedded_chars: int = 80) -> tuple[str, str]:
    """Prefer embedded text; fall back to quality-aware Hindi+English OCR."""
    embedded = extract_embedded_pdf_text(pdf_path)
    if len("".join(embedded.split())) >= min_embedded_chars:
        return embedded, "embedded-text"

    pages = render_pdf(pdf_path, work_dir)
    page_texts = [ocr_image(page) for page in pages]
    text = "\n\n".join(page_texts)
    return correct_ocr_text(text), "tesseract-hin+eng-quality-aware"
