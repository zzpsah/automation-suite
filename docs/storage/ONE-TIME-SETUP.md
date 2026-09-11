# UMV Storage — One-Time Setup

This is the only setup that requires a human. After it is completed, file upload, backup, verification and retry are automated.

## 1. Cloudflare R2

Create a Cloudflare account using the available sign-in options (GitHub login is supported by Cloudflare). Enable R2 and create a **private** bucket for UMV intake files.

Create an R2 S3 API credential restricted to this bucket with only the permissions needed by the uploader (normally object read/write). Record:

- `R2_ENDPOINT`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`

Do not put the secret key in GitHub source files or Telegram messages.

## 2. Backblaze B2

Create a Backblaze account and a **private** B2 bucket dedicated to UMV backups.

Create an application key restricted to that bucket and only the required read/write operations. Record:

- `B2_ENDPOINT`
- `B2_ACCESS_KEY_ID`
- `B2_SECRET_ACCESS_KEY`
- `B2_BUCKET`

## 3. Secret storage

The implementation must keep credentials in server-side secret stores. Recommended locations:

- Supabase Edge Function secrets for runtime file ingestion.
- GitHub Actions repository secrets for scheduled health/reconciliation jobs.

Never commit these values to the repository.

## 4. Expected GitHub repository secrets

```text
R2_ENDPOINT
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET
B2_ENDPOINT
B2_ACCESS_KEY_ID
B2_SECRET_ACCESS_KEY
B2_BUCKET
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET
AUTHORIZED_TELEGRAM_USER_IDS
```

Existing secrets should be reused where already configured; do not duplicate or expose secret values.

## 5. Completion test

After credentials are configured, automation should perform a small private test object upload to R2 and B2, verify the object, calculate/compare SHA-256, and remove the test object. The production pipeline is not considered storage-ready until both providers pass this test.

## Human involvement after setup

None for normal files. The system owns upload, backup, verification, retry and reconciliation. A human is only involved for unrecoverable account/provider/security problems.
