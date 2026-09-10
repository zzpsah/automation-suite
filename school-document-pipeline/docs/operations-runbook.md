# Operations Runbook

## Daily ingest

1. Authorized Telegram files arrive through one-minute polling, or files are placed in the private Drive Inbox.
2. The worker validates the source and moves accepted files to Processing.
3. The original filename is preserved wherever possible.
4. The worker records source metadata, attachment metadata, duplicate identity, and processing status in Supabase.
5. `MANUAL_ONLY` creates a review record without guessing document contents.
6. Current Drive OCR processes images and entire PDFs. Strict first-page processing remains pending.

## Portal-facing filename and description

The original filename is source evidence. A reviewer may approve a separate `display_filename` and concise portal description after checking the first page.

Suggested display filename:

```text
YYYY-MM-DD__Office__Reference__Short-Subject.pdf
```

If a date, office, reference, or subject is missing, keep the original filename and mark the suggestion `Needs Manual Review`. Never invent missing values.

Example description:

```text
Official Education Department instruction regarding Class XI registration correction. The school must verify student details before the printed deadline.
```

The private portal currently displays the stored display filename. The worker stores suggested filenames separately and may update metadata from extraction. Human acceptance controls and automatic Drive renaming are not implemented. Public publication still requires approval.

## Gemini review gate

Gemini is optional. When enabled, it returns structured first-page suggestions. A reviewer must confirm them against the original page before updating metadata or renaming a display copy. Gemini must not submit forms, pay fees, forward documents, publish records, or delete files.

## Review

Reviewers confirm the message date, sender, document title, issuing office, reference number, deadline, required action, related school/student/teacher, amount, category, priority, and duplicate status. Missing information stays null or is marked `Needs Manual Review`.

## Category changes

Use the immutable `category_key`. Change labels and matching terms by creating a new category-definition version. Never rewrite or delete an old definition merely because the website navigation changed.

## Search

Search the structured fields and the generated search text. Useful searches include office name, reference number, deadline, student, registration, fee, examination, UDISE, inspection, portal, and action terms. Search results must still be reviewed against the original message or attachment.

## Publication

Records stay private until an authorized reviewer marks them approved. The public view excludes unapproved, duplicate, sensitive, and internal records. The GitHub Pages portal has no delete or edit authority over source data.

## Retry and recovery

- `New` or `Processing Failed`: inspect the event log, then retry the source file.
- `Needs Manual Review`: review the original Drive file and update metadata.
- `Duplicate`: keep the main record and record where the duplicate appeared.
- `Archived`: retain the record for audit; do not remove it from history automatically.

## What must never be automated without approval

- Sending or forwarding school documents.
- Deleting Drive files or database rows.
- Paying fees or submitting official forms.
- Publishing student, staff, financial, or private administrative data.
- Sharing secrets, tokens, OTPs, or private Drive links.
