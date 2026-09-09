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

1. Create private Drive folders: Inbox, Processing, Reviewed, Duplicates, Ignored, Manual Review, Archive.
2. Create an Apps Script project.
3. Add Drive as an advanced service.
4. Put IDs and secrets in Apps Script Properties.
5. Deploy the private review web app only after access settings are reviewed.

## Phase 4: Telegram

Create a private bot. Enter the token directly into Apps Script Properties. Configure authorized Telegram user/chat IDs before registering the webhook.

## Phase 5: portal

Integrate only with the verified staging website. Production requires separate approval.
