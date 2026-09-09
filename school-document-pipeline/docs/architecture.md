# Architecture

## Data flow

```text
Telegram Bot ----┐
                 ├─> Apps Script ingestion -> private Google Drive
Drive Inbox -----┘             |
                               v
                   extraction and duplicate checks
                               |
                               v
                         Supabase metadata
                         /               \
              private review       approved_public_documents
                                           |
                                           v
                                  GitHub-hosted portal
```

## Drive layout

```text
My Drive/
└── All Education Department Letters/
    └── Automation System/
        ├── 01_Inbox/             # newly received Telegram or Drive files
        ├── 02_Processing/        # registered files awaiting review
        ├── 03_Reviewed_Archive/  # reviewed private records
        └── 04_Manual_Review/     # unclear files needing human review
```

Moving these folders does not change their Drive IDs, so Apps Script properties remain valid after reorganization.

## Component responsibilities

| Component | Responsibility | Write authority |
| --- | --- | --- |
| Telegram bot | Receive an authorized document or image | Telegram message only |
| Apps Script webhook | Validate, download, and preserve originals | Private Drive and Supabase |
| Drive folders | Preserve originals and review-stage organization | Apps Script plus reviewer |
| Supabase | Store metadata, events, categories, duplicates, and status | Server-side integration and reviewer |
| Gemini adapter | Optional first-page suggestions | Never publishes or deletes automatically |
| GitHub Pages portal | Display approved public-safe records | No source-data write authority |

## New-document lifecycle

```text
Telegram upload
  -> webhook validates secret and allowlist
  -> original saved in 01_Inbox
  -> Supabase metadata row created
  -> file moved to 02_Processing
  -> optional first-page extraction suggestion
  -> human review confirms fields and action
  -> file moves to Reviewed Archive or Manual Review
  -> only approved safe records appear on the portal
```

The clean-start procedure is review-first: identify exact test rows and files, then delete only explicitly approved test data. Credential rotation never requires deleting document history.

## Boundaries

BrowserAct remains an independent reusable browser automation module. A future adapter may import BrowserAct-collected files, but ingestion, storage, review, and publication do not depend on it.

The public portal never receives Telegram identifiers, OCR text, private Drive IDs, internal notes, or service credentials. All write operations happen through protected server-side components.

## Processing states

`New -> Queued -> Processing -> Needs Manual Review -> Reviewed -> Approved -> Published`

Alternative endings: `Duplicate`, `Ignored`, `Archived`, or `Processing Failed`.

## Extraction

Default mode is `MANUAL_ONLY`. It creates review records without guessing document contents. Optional AI implementations must conform to the same extraction-result schema and cannot publish, rename, delete, or forward records automatically.

## Optional Gemini document assistant

Gemini can provide first-page suggestions for a title, issuing authority, date, reference number, subject, deadline, required action, category, priority, portal description, and safe display filename. The original filename and original file remain unchanged until a reviewer approves any suggestion.

The adapter must store the model name, prompt version, timestamp, confidence, and review decision. Keep the Gemini key server-side and do not send sensitive files by default.
