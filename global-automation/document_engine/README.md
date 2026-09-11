# Global Document Processing Engine

Reusable document-understanding layer built on **Global Sarkari OCR**. It is a separate platform component, not School Document Pipeline code.

## Stable API

```python
from document_engine import process
result = process("document.pdf", "/tmp/document-work")
```

The engine composes OCR, extraction, metadata, classification, summary and confidence. Consumers do not import OCR backend internals.

## Separation contract

- Global OCR owns image/PDF text extraction, preprocessing, correction, language packs, backend adapters, diagnostics, training and benchmarks.
- Global Document Engine owns document understanding on top of OCR evidence.
- School Document Pipeline is only a consumer.
- Telegram, Supabase, portal automation and future projects may consume the same interface.
- Original OCR evidence is preserved; derived fields never overwrite source text.
- No publication, approval or deletion decision is made by this engine.
