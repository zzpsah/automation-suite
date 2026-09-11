# Global Sarkari OCR

Reusable OCR and government-document language normalization layer for the school and future government-document automation projects.

## Goals

- Hindi + English OCR using open-source Tesseract on GitHub Actions/Linux.
- Preserve raw OCR text as evidence.
- Normalize common Sarkari document labels without changing source meaning.
- Extract structured fields such as authority, subject, reference number, date, office, department, action, deadline and category.
- Keep original wording and a normalized administrative representation separately.
- Support Bihar government / education terminology first, while remaining reusable for other departments and states.
- Never treat OCR output as authoritative when confidence is low.

## Design

```text
PDF / Image
   |
   +--> embedded text extraction
   |
   +--> page rendering (when needed)
   |
   +--> Tesseract hin+eng
   |
   +--> OCR cleanup
   |
   +--> Sarkari label/phrase normalization
   |
   +--> structured metadata
   |
   +--> confidence + evidence
   |
   +--> consumer (Supabase / archive / workflow)
```

## Language policy

The normalizer is not a translator. It should:

1. preserve the original OCR text;
2. identify labels and fields in Hindi/English;
3. normalize spelling/spacing and known administrative variants;
4. prefer exact document wording for subject and authority;
5. use controlled terminology only where the source supports it;
6. never invent dates, reference numbers, authorities or actions.

## Initial terminology families

Examples to support as the project grows:

- विषय / विषयक / Subject
- पत्रांक / ज्ञापांक / पत्र संख्या / क्रमांक / Reference No.
- दिनांक / दिनांकित / Date
- प्रेषक / प्रेषित / जारीकर्ता / Issuing Authority
- कार्यालय / Office
- विभाग / Department
- प्रति / प्रतिलिपि / Copy to
- सूचना / आदेश / पत्र / अधिसूचना / ज्ञापन
- नामांकन / प्रवेश / परीक्षा / परिणाम / छात्र / शिक्षक
- बिहार विद्यालय परीक्षा समिति / BSEB
- शिक्षा विभाग / शिक्षा विभाग, बिहार

## Relationship to the document processor

The existing `global-automation/scripts/document/document_processor.py` remains the production consumer during migration. This directory is the reusable OCR layer; it should not require the school-specific database schema.

Tesseract is installed by CI/runtime rather than committed as a binary into GitHub.
