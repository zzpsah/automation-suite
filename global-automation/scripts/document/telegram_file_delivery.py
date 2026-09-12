"""Prepare safe Telegram delivery files without relabelling bytes as PDF."""
from __future__ import annotations

import io
import mimetypes
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter

PDF_MAGIC = b"%PDF-"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
OFFICE_EXTS = {".doc", ".docx", ".odt", ".rtf", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp"}


def detect_format(data: bytes, filename: str = "", mime_type: str = "") -> str:
    """Prefer content signatures over filename extensions."""
    if data.startswith(PDF_MAGIC):
        return "pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        return "webp"
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in OFFICE_EXTS:
        return "office"
    if mime_type == "application/pdf":
        return "unknown"
    return "unknown"


def validate_pdf(data: bytes) -> int:
    if not data.startswith(PDF_MAGIC):
        raise ValueError("delivery is not a real PDF (missing %PDF signature)")
    reader = PdfReader(io.BytesIO(data), strict=False)
    if not reader.pages:
        raise ValueError("PDF contains zero pages")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    return len(reader.pages)


def image_to_pdf(data: bytes) -> tuple[bytes, int]:
    src = Image.open(io.BytesIO(data))
    frames = []
    n = getattr(src, "n_frames", 1)
    for i in range(n):
        if n > 1:
            src.seek(i)
        img = src.convert("RGB")
        canvas = Image.new("RGB", (1240, 1754), "white")
        img.thumbnail((1176, 1690), Image.Resampling.LANCZOS)
        canvas.paste(img, ((1240 - img.width) // 2, (1754 - img.height) // 2))
        frames.append(canvas)
    out = io.BytesIO()
    frames[0].save(out, format="PDF", resolution=150.0, save_all=True, append_images=frames[1:])
    result = out.getvalue()
    pages = validate_pdf(result)
    return result, pages


def office_to_pdf(data: bytes, filename: str) -> tuple[bytes, int]:
    suffix = Path(filename).suffix.lower()
    if suffix not in OFFICE_EXTS:
        raise ValueError("unsupported office extension")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / (Path(filename).stem + suffix)
        src.write_bytes(data)
        proc = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(src)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        target = src.with_suffix(".pdf")
        if proc.returncode != 0 or not target.exists():
            raise RuntimeError(f"LibreOffice conversion failed: {(proc.stderr or proc.stdout).strip()[:500]}")
        result = target.read_bytes()
        pages = validate_pdf(result)
        return result, pages


def prepare_delivery(data: bytes, filename: str, mime_type: str = "") -> dict:
    """Return validated delivery bytes and the true delivery format."""
    kind = detect_format(data, filename, mime_type)
    if kind == "pdf":
        pages = validate_pdf(data)
        output_name = filename if filename.lower().endswith(".pdf") else Path(filename).stem + ".pdf"
        return {"data": data, "filename": output_name, "mime_type": "application/pdf", "source_format": "pdf", "delivery_format": "pdf", "converted": False, "pages": pages}
    if kind in {"jpeg", "png", "tiff", "webp", "image"}:
        converted, pages = image_to_pdf(data)
        return {"data": converted, "filename": Path(filename).stem + ".pdf", "mime_type": "application/pdf", "source_format": kind, "delivery_format": "pdf", "converted": True, "pages": pages}
    if kind == "office":
        converted, pages = office_to_pdf(data, filename)
        return {"data": converted, "filename": Path(filename).stem + ".pdf", "mime_type": "application/pdf", "source_format": Path(filename).suffix.lower().lstrip("."), "delivery_format": "pdf", "converted": True, "pages": pages}
    guessed = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return {"data": data, "filename": filename or "document", "mime_type": guessed, "source_format": "unknown", "delivery_format": "original", "converted": False, "pages": None}
