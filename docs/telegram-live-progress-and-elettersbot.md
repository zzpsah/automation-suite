# Telegram live progress + eLettersBot delivery contract

## Input progress

Each file received by `telegram-input-v2` gets a persistent progress message in the same Telegram chat. The message is updated from the real `telegram_intake` and linked `documents` state; the bot does not invent progress.

```text
1 Telegram intake
2 Intake saved
3 B2 upload
4 B2 verification
5 Processor link / GitHub dispatch
6 GovDOC OCR
7 Metadata
8 Publication
9 Telegram delivery
```

`telegram-progress` edits the same message after intake state changes. `/status <UUID>`, `/today`, `/failed` and `/health` expose the same state for manual diagnosis. A failure is shown with the failed stage and the real stored processor error.

## eLettersBot file contract

The delivery worker must never rename arbitrary bytes to `.pdf`.

- Real PDFs are structurally validated with `pypdf` before upload.
- JPEG/PNG/TIFF/WebP images are converted to a real A4 PDF with preserved aspect ratio and validated again.
- DOC/DOCX/ODT/RTF/XLS/XLSX/ODS/PPT/PPTX/ODP are converted with LibreOffice and validated.
- Unsupported types keep their original format and MIME type instead of being presented as a PDF.
- Source SHA-256 is checked against the stored intake checksum before preparation.
- Delivery SHA-256, source format, delivery format, conversion flag, page count and filename are written to the Telegram delivery audit.
- Captions use cleaned metadata fields and omit empty fields; raw OCR fragments are not used as prose.

## Operational invariants

GovDOC OCR remains the canonical OCR engine. The delivery fix is downstream of OCR and does not modify OCR behavior. B2 remains the primary file store and Google Drive remains backup/public delivery storage.
