# Architecture

## Repository model
This is a monorepo-style automation suite with multiple independent modules and shared GitHub workflows.

## Observed top-level areas
- `android-document-scanner/`
- `browser-portal-automation/`
- `global-automation/`
- `paint-gemini-app/`
- `phone-printer/`
- `school-document-pipeline/`
- `docs/`
- `.github/workflows/`
- `.claude/`

Each module may have different runtime, security, deployment, and data boundaries. Read module-local docs and code before making cross-module assumptions.
