# Telegram Setup

This document records the Telegram portion of the School Document Pipeline. It is intentionally written so the workflow can be repeated if the website, Apps Script project, or portal layout changes.

## What is already prepared

- Apps Script contains `TelegramWebhook.gs` and the shared ingestion modules.
- The private Drive Inbox and Processing folders are configured.
- Supabase tables and RLS are deployed.
- The public portal is read-only and does not receive Telegram tokens or private Drive identifiers.

## Create the bot

1. Log in to Telegram Web or use the Telegram mobile application.
2. Open the verified `@BotFather` account.
3. Send `/newbot`.
4. Choose a display name, for example `School Document Intake`.
5. Choose an unused username ending in `bot`, for example `SchoolDocumentIntakeBot`.
6. BotFather returns a token. Treat it as a password.

Never commit the token to GitHub, place it in the public portal, paste it into a chat, or store it in a normal Supabase table. The token belongs only in Apps Script Project Settings → Script Properties as `TELEGRAM_BOT_TOKEN`.

## Configure private properties

Add these values in Apps Script Project Settings. Do not put real values in `.env.example`:

```text
TELEGRAM_BOT_TOKEN=<BotFather token>
TELEGRAM_WEBHOOK_SECRET=<long random secret>
AUTHORIZED_TELEGRAM_USER_IDS=<comma-separated numeric IDs>
AUTHORIZED_TELEGRAM_CHAT_IDS=<comma-separated numeric IDs>
DRIVE_INBOX_FOLDER_ID=<private Inbox folder ID>
DRIVE_PROCESSING_FOLDER_ID=<private Processing folder ID>
SUPABASE_URL=<Supabase project URL>
SUPABASE_SERVER_SECRET=<server-only Supabase secret>
EXTRACTION_MODE=MANUAL_ONLY
DRIVE_SCAN_BATCH_SIZE=10
```

The webhook secret is an application secret, not a Supabase API key. Do not invent a Supabase key. Use the project's real server secret only in Apps Script Properties.

## Deploy and register the webhook

1. Run `installDriveScanTrigger` once and verify the time-based `scanDriveInbox` trigger.
2. Deploy Apps Script as a web app owned by the account that owns the private Drive folders.
3. Keep the web app access as restrictive as the Telegram webhook design permits.
4. Register the web-app URL with Telegram's `setWebhook` API using the bot token and webhook secret.
5. Send one synthetic, non-sensitive test file.
6. Verify that the file is saved in Drive, a Supabase metadata row is created, and the item remains private until review.

## Failure handling

- Missing or invalid webhook secret: reject the request.
- Unauthorized Telegram user or chat: reject the request.
- Unsupported media: record the failure and do not guess its contents.
- Duplicate Telegram message: do not create a second document record.
- Drive or Supabase failure: leave the source available for retry and record the failure event.

## Token rotation

If the token is exposed, use BotFather `/revoke`, replace `TELEGRAM_BOT_TOKEN` in Apps Script Properties, and register the webhook again. Do not delete database history merely because a credential was rotated.
