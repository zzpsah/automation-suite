# Session — 2026-09-18 — UDISE Student Profile Automation

## Scope
Implement the first safe automation layer for individual UDISE+ student profiles:
- General Profile (GP)
- Education Profile (EP)
- Facility Profile (FP)

This is not the School Profile GP/EP workflow.

## Branch
`feature/udise-student-profile-automation`

No merge to `main` and no production deployment performed.

## Implemented
- New module under `browser-portal-automation/udise/student-profile/`.
- BrowserAct CLI wrapper using shell-safe argv execution.
- BrowserAct doctor command.
- Guided one-student read-only discovery flow.
- Fresh state capture before each click to avoid stale indexes.
- GP/EP/FP state + rendered Markdown evidence capture.
- Private checkpointing.
- Minimal operational audit JSONL.
- Field comparison engine.
- Preview-only proposed-change generation.
- Empty discovery-required schemas for GP/EP/FP.
- Comparison unit tests with synthetic values.
- Runtime private-data path ignored by Git.
- APPLY and SUBMIT commands intentionally blocked.

## Authentication/security
- User performs login/CAPTCHA/OTP/MFA.
- No bypass functionality implemented.
- No secrets/session material stored in Git.

## Required live verification
1. User logs into UDISE+ normally.
2. Run BrowserAct against that authenticated session.
3. Open one test student.
4. Capture GP, EP and FP read-only.
5. Inspect exact fields, controls and stable locators.
6. Populate schemas from observed evidence.
7. Only after verification, design write-enabled APPLY and separate SUBMIT gates.

## Source priority for Class XI EP
OFSS → e-Shiksha Kosh → UDISE current status → Siwan Dropbox fallback/history.

This is a reconciliation/proposal priority, not permission to overwrite source snapshots.
