# Setup Guide

## Phase 1: repository

Run the synthetic validation tests and review the proposed SQL migration. Do not use real student or staff records.

## Phase 2: Supabase staging

1. Select the exact non-production Supabase project.
2. Review `supabase/migrations/0001_document_pipeline.sql`.
3. Apply through the supported Supabase migration workflow.
4. Run security and performance advisors.
5. Verify anonymous access returns only approved public-safe records.

## Phase 3: Google

1. Use the four folders under `All Education Department Letters/Automation System`: `01_Inbox`, `02_Processing`, `03_Reviewed_Archive`, `04_Manual_Review`.
2. Create an Apps Script project.
3. Add Drive as an advanced service.
4. Put IDs and secrets in Apps Script Properties.
5. Deploy the private review web app only after access settings are reviewed.

Set `DRIVE_SCAN_BATCH_SIZE` to a value from 1-50 (start with 10). A successfully registered file is moved from Inbox to Processing. A failed file stays in Inbox so it remains visible for retry or manual review.

`DRIVE_OCR` currently accepts images and PDFs and converts the full PDF to a temporary Google Doc, then trashes that temporary conversion. It does not yet enforce first-page-only processing. Use `MANUAL_ONLY` when full-document OCR is unsuitable. Original PDFs are preserved.

## Phase 4: Telegram

Enter the bot token directly into Apps Script Properties and configure authorized Telegram user/chat IDs. Run `installTelegramPolling` once; it installs a one-minute trigger and disables the webhook without dropping pending updates. Do not register the legacy webhook while polling is active.

## Phase 5: portal

Integrate only with the verified staging website. Production requires separate approval.

Open `private-documents.html` with the existing admin login. Public Supabase configuration lives in `assets/document-archive-config.js`; never put server credentials there. The final queue authorization migration is `20260910132000_review_request_authorization.sql`. Use `configureFreeReviewMode` to select `RULES` with `DRIVE_OCR` and install the five-minute worker. The current free mode is already configured. See [current deployment](current-deployment.md) before replaying setup steps.
