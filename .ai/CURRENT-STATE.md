# Current State

Last verified: 2026-09-14

## Verified repository state
- Default branch: `main`.
- Onboarding baseline HEAD: `d570775c0a07278ab0380246f3728c94caf85998`.
- Baseline commit message: `fix(scanner): import Compose setContent`.
- Root includes `.claude/`, `CLAUDE.md`, `.github/workflows/`, and multiple independent automation/application modules.
- Observed modules include `android-document-scanner/`, `browser-portal-automation/`, `global-automation/`, `paint-gemini-app/`, `phone-printer/`, and `school-document-pipeline/`.
- DevOS `.ai/` is being added without replacing module-specific documentation.

## DevOS / Windows Work Browser retirement
- The previous Windows Work Browser / Browser Automation prototype was declared a failed implementation and retired.
- Its source tree, dedicated CI/release workflows, and project-specific files were removed from `main`.
- All old development branches associated with that prototype were subsequently removed; final branch audit found no matching Work Browser branches.
- The old preview release/tag was also manually removed by the repository owner.
- Do not reuse, revive, or silently depend on that retired prototype architecture.
- A future DEVOS browser project must start from a clean architecture: custom DEVOS application shell and UX, Chromium only as an underlying browser engine where appropriate, built-in command/agent runtime, browser + Windows desktop automation, workflow/checkpoint/recovery, file/PDF/image tooling, and MCP integration.

## Safety
- Identify module scope before changes.
- Keep credentials/private school documents out of public repository context.
- External/production mutations require explicit authorization.

## Last automated change
- Commit: `9b403ac919155d414d5ba53692fbea9abb093a06`
- Change: `chore: remove failed Windows Work Browser prototype`
- Date: `2026-09-14`
- Durable context synchronization: updated on 2026-09-14 to record complete retirement of the failed prototype.
