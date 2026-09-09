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

## Boundaries

BrowserAct remains an independent reusable browser automation module. A future adapter may import BrowserAct-collected files, but ingestion, storage, review, and publication do not depend on it.

The public portal never receives Telegram identifiers, OCR text, private Drive IDs, internal notes, or service credentials. All write operations happen through protected server-side components.

## Processing states

`New -> Queued -> Processing -> Needs Manual Review -> Reviewed -> Approved -> Published`

Alternative endings: `Duplicate`, `Ignored`, `Archived`, or `Processing Failed`.

## Extraction

Default mode is `DRIVE_OCR`. `MANUAL_ONLY` works without any AI key. Optional AI implementations must conform to the same extraction-result schema and cannot publish records automatically.
