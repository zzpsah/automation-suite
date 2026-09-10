# Review tools and Telegram delivery

## Incident: 10 September 2026

BrowserAct verified the live Telegram error `Wrong response from the webhook:
302 Found`, with four pending updates. Deployment version 3 suppresses repeated
duplicate replies. `TelegramPolling.gs` replaces webhook delivery with an Apps
Script minute trigger: `installTelegramPolling` installs one trigger and calls
`deleteWebhook` with `drop_pending_updates:false`. Offsets advance only after
successful handling or an explicitly rejected unauthorized sender. Re-running
installation does not duplicate triggers. Do not run `registerTelegramWebhook`
while polling is enabled. Trigger executions use saved editor code; no web-app
redeployment is required for polling changes.

## Review configuration

The seven suggestion columns were applied and verified in Supabase. The adapter
code is saved in the live Apps Script editor used by polling. Provider activation
and an end-to-end extraction test remain separate from this deployment; no AI
key value was inspected or added during the delivery repair.

Set `REVIEW_PROVIDER` in Apps Script Properties to `NONE`, `RULES`, or `GEMINI`.
`RULES` uses the existing extraction result, including Drive image OCR when
`EXTRACTION_MODE=DRIVE_OCR`. Gemini requires `GEMINI_API_KEY` and optionally
`GEMINI_MODEL`. Other services need an adapter in `ReviewAssistant.gs`; they are
not yet implemented. Store credentials only in server-side Script Properties.

All providers produce the same fields: title, authority, printed date, reference,
deadline, action, category, priority, description, display filename, confidence,
and notes. The JSON also records provider and model. Suggestions sync to the
same Supabase document ID in `ai_suggested_json` and companion suggestion fields.
Telegram reports that result after registration. Portal approval and physical
Drive renaming are separate work still to implement; suggestions alone do not
publish or rename a file.

Gemini currently receives the original PDF with a first-page-only instruction.
This is not physical first-page isolation: the entire PDF is uploaded. Strict
first-page-only transmission requires a PDF split/render step before this
adapter and remains pending. Keep Gemini disabled until that limitation is
acceptable for the selected test document.

## Repeated Telegram replies

The old handler sent `Document already registered.` on every delivery of an
existing source message. The patched handler silently acknowledges that repeat
and uses a script lock around the lookup and ingestion. The registration return
value now retains the review suggestion so the Telegram report can include it.

Run `inspectTelegramDelivery` in Apps Script to inspect pending update count
and Telegram's last delivery error without printing the secret webhook URL.
Apps Script ContentService uses a redirect. Telegram retries unsuccessful HTTP
delivery, so check the actual error before claiming the transport is repaired.
Returning `{ok:false}` JSON does not itself set an HTTP error status. This
synchronous handler still needs a durable queue and a direct HTTP-200 ingress
for robust delivery under timeout or transient failures. Never drop pending
updates to conceal the problem.

Deployment checklist: copy updated sources, save, deploy a new version of the
existing deployment, run diagnostics, then send one test attachment and verify
one database record and one confirmation. Repository tests alone do not prove
the live bot is fixed.

References:
- https://core.telegram.org/bots/api#setwebhook
- https://developers.google.com/apps-script/guides/content
