# Automation Suite — AI Development Guide

## Project scope

This repository is the School Document Pipeline plus the reusable GovDOC OCR Engine / GovDOC Vision component.

Current priority:
1. Test GovDOC OCR against real school/government-document cases.
2. Integrate it safely at the School Document Pipeline OCR boundary.
3. Keep the existing production pipeline stable and idempotent.
4. Verify storage -> OCR -> metadata -> Supabase -> publication behavior.

Do not expand GovDOC OCR with new feature work unless the feature is required to complete the integration or fix a verified defect.

## Architecture boundaries

- Supabase is the control-plane source of truth.
- Backblaze B2 is primary file storage.
- Google Drive is backup/public delivery storage.
- Telegram is intake/transport, not long-term storage.
- GovDOC OCR owns OCR, preprocessing, language packs, document intelligence and OCR diagnostics.
- The School Document Pipeline owns intake, storage verification, lifecycle, Supabase writes, publication and notifications.

## Safety rules

- Never invent document metadata when source evidence is missing.
- Never infer school/district/block/office from a person's name alone.
- Preserve original OCR text alongside normalized metadata.
- Handwriting is review-only unless explicitly supported by a tested backend.
- Missing B2 objects must be diagnosed/classified; do not fabricate recovery data.
- Repeated runs must remain safe and idempotent.
- Do not republish merely because delivery failed.
- Do not expose private B2/Drive URLs to Telegram users.
- Do not modify security/RLS in this integration phase unless explicitly requested.

## Development loop

For every production change:
1. Inspect the existing implementation and data contract first.
2. Add or update an offline regression test for the behavior.
3. Make the smallest implementation change that satisfies the test.
4. Run compile/smoke/regression checks.
5. Review the diff for unintended pipeline or publication changes.
6. Update documentation when behavior or recovery steps change.

## Preferred change shape

Keep GovDOC OCR behind the existing adapter boundary. Avoid rewriting the stable document processor merely to introduce OCR behavior.

## Verification priority

A green offline test is not proof of production storage health. Production verification must separately establish that the B2 object exists, can be downloaded, reaches the OCR boundary, produces metadata, and creates/updates the expected Supabase record.
