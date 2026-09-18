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

## Browser portal automation
`browser-portal-automation/` uses BrowserAct as a reusable authenticated-browser control layer.

Durable interaction rule:
1. Capture fresh page state.
2. Identify the current element/index.
3. Perform one action.
4. Wait for stability.
5. Capture fresh state again.

Never persist/reuse BrowserAct state indexes across navigation or page mutation.

## UDISE individual Student Profile automation

Module:

```text
browser-portal-automation/udise/student-profile/
```

Profile scope:
- General Profile (GP)
- Education Profile (EP)
- Facility Profile (FP)

### Runtime stages
```text
SCAN -> COMPARE -> PREVIEW -> APPLY -> SUBMIT
```

Current implementation supports:
- SCAN/discovery
- COMPARE
- PREVIEW

Current implementation intentionally blocks:
- APPLY
- SUBMIT

### Authentication boundary
Authentication is a human handoff boundary:
- user enters credentials,
- user completes CAPTCHA,
- user completes OTP/MFA/security confirmation,
- automation continues only after legitimate authenticated access.

Do not bypass security mechanisms or persist sensitive session material in the repository.

### Discovery-first schema model
The portal's real field inventory and stable locators must be observed before writing automation.

Schema files:
- `general_profile.schema.json`
- `education_profile.schema.json`
- `facility_profile.schema.json`

These remain empty/marked discovery-required until verified from live authenticated pages.

### Evidence and checkpoints
Private runtime output is written beneath the module's `runtime/` directory and is Git-ignored.

Runtime evidence may contain student data and therefore must remain local/private.

Checkpointing records the last completed stage so an interrupted browser session can resume safely after the user logs in again.

### Data/reconciliation boundary
Portal snapshots and approved master data are compared without mutating source snapshots.

For Class XI Education Profile proposals, the intended source priority is:
1. OFSS for admission details.
2. e-Shiksha Kosh as secondary.
3. UDISE as current enrollment/status reference.
4. Siwan Dropbox as fallback/history/import reference.

Conflicts remain visible and require review.

### Write safety
Future APPLY must:
- operate only on reviewed/approved fields,
- record old/proposed/final values,
- stop on selector/schema uncertainty,
- never infer approval from a previous run.

Future SUBMIT must:
- be a separate action,
- require explicit authorization,
- never be implied by APPLY approval.
