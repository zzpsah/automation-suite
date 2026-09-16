from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.request
from pathlib import Path


def enrich(ocr_text: str, deterministic_metadata: dict, evidence_images: list[str] | None = None) -> dict | None:
    """Optional multimodal Gemini enrichment. Disabled unless GEMINI_API_KEY is configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not ocr_text.strip():
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = """You are a conservative government-document metadata extractor. Return JSON only. Never invent missing facts. Use the supplied page images as primary visual evidence and OCR as supporting evidence. Preserve names, dates, reference numbers, codes and official wording exactly when supported. If OCR conflicts with the image, prefer what is visibly legible and record uncertainty in review_fields. Do not rewrite the source document.\n\nSchema: {\"subject\": string|null, \"document_type\": string|null, \"issuing_authority\": string|null, \"document_date\": string|null, \"reference_number\": string|null, \"description\": string|null, \"entities\": [{\"type\": string, \"value\": string}], \"topics\": [string], \"review_fields\": [string]}\n\nDeterministic metadata:\n""" + json.dumps(deterministic_metadata, ensure_ascii=False) + "\n\nOCR:\n" + ocr_text
    parts = [{"text": prompt}]
    for image_path in evidence_images or []:
        path = Path(image_path)
        if not path.exists():
            continue
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(path.read_bytes()).decode("ascii")}})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("AI enrichment returned a non-object")
    return result
