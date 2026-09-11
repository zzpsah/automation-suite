# Global Automation Toolkit

Reusable PowerShell scripts and GitHub Actions for remote administration of automation services.

## Current modules

- Telegram webhook diagnostics and configuration
- Supabase REST health check

## GitHub Actions

Run from **Actions** → choose a workflow → **Run workflow**.

Required repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `AUTHORIZED_TELEGRAM_USER_IDS`

Secrets are never stored in source files.

## Telegram input bot

Default webhook target used by the workflow:

`https://sxfnrwugsyfypqgfglzc.supabase.co/functions/v1/telegram-input-v2`

The webhook workflow accepts another URL through its manual `webhook_url` input if needed.
