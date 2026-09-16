from __future__ import annotations

import json
import os
import urllib.request


def enrich(ocr_text: str, deterministic_metadata: dict) -> dict | None:
    """Optional Gemini enrichment. Disabled unless GEMINI_API_KEY is configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not ocr_text.strip():
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = """You are a conservative government-document metadata extractor. Return JSON only. Never invent missing facts. Preserve names, dates, reference numbers and official wording exactly when supported by the supplied OCR. If a field is uncertain, set it to null and add the field name to review_fields. Do not rewrite the source document.\n\nSchema: {\"subject\": string|null, \"document_type\": string|null, \"issuing_authority\": string|null, \"document_date\": string|null, \"reference_number\": string|null, \"description\": string|null, \"entities\": [{\"type\": string, \"value\": string}], \"topics\": [string], \"review_fields\": [string]}\n\nDeterministic metadata:\n""" + json.dumps(deterministic_metadata, ensure_ascii=False) + "\n\nOCR:\n" + ocr_text
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("AI enrichment returned a non-object")
    return result
