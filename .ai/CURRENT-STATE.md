# Current State

Last verified: 2026-09-13

## Verified repository state
- Default branch: `main`.
- Onboarding baseline HEAD: `d570775c0a07278ab0380246f3728c94caf85998`.
- Baseline commit message: `fix(scanner): import Compose setContent`.
- Root includes `.claude/`, `CLAUDE.md`, `.github/workflows/`, and multiple independent automation/application modules.
- Observed modules include `android-document-scanner/`, `browser-portal-automation/`, `global-automation/`, `paint-gemini-app/`, `phone-printer/`, and `school-document-pipeline/`.
- DevOS `.ai/` is being added without replacing module-specific documentation.

## Safety
- Identify module scope before changes.
- Keep credentials/private school documents out of public repository context.
- External/production mutations require explicit authorization.

## Last automated change
- Commit: aae30b1652e681831dde8f94ba5ace4870a62652
- Change: fix(scanner): apply flash changes without camera rebind
- Date: 2026-09-13
- Durable context synchronization: completed
