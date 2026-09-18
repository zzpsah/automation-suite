# Current State

Last verified: 2026-09-18

## Verified repository state
- Default branch: `main`.
- Active implementation branch for UDISE student-profile automation: `feature/udise-student-profile-automation`.
- Root contains multiple independent modules including `browser-portal-automation/`.
- The existing reusable BrowserAct portal pattern remains the browser-control baseline for authenticated government/school portals.
- No production deployment or merge to `main` has been performed for this feature branch.

## UDISE Student Profile automation
A new module exists at:

```text
browser-portal-automation/udise/student-profile/
```

Scope is **individual student profiles**, specifically:
- General Profile (GP)
- Education Profile (EP)
- Facility Profile (FP)

The first implementation is read-only first:
- `doctor`: verify BrowserAct/session reachability.
- `discover-one`: guided discovery for exactly one test student after manual authentication.
- captures fresh BrowserAct state before every click so stale state indexes are never reused.
- captures GP/EP/FP page state + Markdown evidence.
- writes private runtime checkpoints and audit metadata under a Git-ignored runtime directory.
- `compare`: compares extracted portal values with an approved source JSON.
- `preview`: produces proposed changes without writing to the portal.
- `apply` and `submit` are intentionally blocked in this first phase.\n- A Windows Tkinter GUI (`gui.py` + `run_gui.bat`) now wraps connection check, guided discovery, compare, preview, and runtime-folder access.

## Safety
- Login, password, CAPTCHA, OTP/MFA and security confirmations remain human-completed.
- No security-control bypass is implemented.
- No passwords, cookies, session tokens, OTPs, private browser profiles or student exports may be committed.
- Runtime evidence/checkpoints are Git-ignored.
- Source snapshots are treated as immutable.
- Any future APPLY/SUBMIT support must use explicit approval gates and separate submit authorization.

## Next verification
- Run the module in an authenticated UDISE+ session.
- Inspect one real test student read-only.
- Populate the GP/EP/FP field schemas only from observed portal fields and stable locators.
- Validate navigation behavior and field extraction before considering write-enabled automation.

## Last automated change
- Commit: c1a23cd1af4e6afb208963268c2f7a3e3d553126
- Change: feat: add UDISE student GP EP FP automation scaffold
- Date: 2026-09-18
- Durable context synchronization: completed
