# UDISE+ Student Profile Automation

Safe automation scaffold for **individual student profiles** in UDISE+:

- General Profile (GP)
- Education Profile (EP)
- Facility Profile (FP)

This module is intentionally **read-only first**. The first supported workflow is guided discovery and extraction for one test student after the user completes normal login, CAPTCHA, OTP/MFA, or other security confirmation.

## Safety contract

- The user completes authentication and security challenges.
- Never bypass CAPTCHA, OTP, MFA, access controls, or portal protections.
- Never store passwords, cookies, tokens, OTPs, or private browser profiles in Git.
- `SCAN` and `COMPARE` are enabled.
- `PREVIEW` prepares proposed changes only.
- `APPLY` and `SUBMIT` are blocked by default and require explicit future implementation plus runtime approval gates.
- Source snapshots remain immutable.
- No private student data belongs in this public repository.

## First run

Prerequisites:

```powershell
uv tool install browser-act-cli --python 3.12
browser-act --version
browser-act get-skills core --skill-version 2.0.2
```

After you manually log in to UDISE+ in the BrowserAct-controlled Chrome session:

```powershell
python browser-portal-automation/udise/student-profile/runner.py doctor --session udise-profile
python browser-portal-automation/udise/student-profile/runner.py discover-one --session udise-profile --student-label TEST-STUDENT
```

The guided discovery command:

1. captures the authenticated student-list state,
2. asks which current BrowserAct state index opens the chosen test student,
3. captures the student landing page,
4. asks which current index opens GP,
5. captures GP state + Markdown,
6. repeats for EP,
7. repeats for FP,
8. writes a checkpoint and read-only evidence bundle.

Because BrowserAct state indexes are temporary, the script refreshes state before every click and never reuses a stale index.

Output defaults to:

```text
browser-portal-automation/udise/student-profile/runtime/
  checkpoints/
  evidence/
  audit/
  comparisons/
```

The `runtime/` directory is ignored by Git and must remain private.

## Field schema

After discovery, define stable field locators in:

- `schemas/general_profile.schema.json`
- `schemas/education_profile.schema.json`
- `schemas/facility_profile.schema.json`

The schema is deliberately empty/synthetic initially. Do not guess portal fields. Populate it only from actual observed UDISE+ pages.

Each field supports:

```json
{
  "key": "father_name",
  "label": "Father Name",
  "section": "Basic Details",
  "control_type": "text",
  "locator": {
    "strategy": "label",
    "value": "Father Name"
  },
  "editable": true,
  "required": true,
  "normalizer": "text"
}
```

## Compare mode

A source JSON may contain approved master values:

```json
{
  "student_key": "synthetic-key",
  "general": {
    "father_name": "EXAMPLE"
  },
  "education": {},
  "facility": {}
}
```

Compare:

```powershell
python browser-portal-automation/udise/student-profile/runner.py compare ^
  --portal-snapshot private-portal-snapshot.json ^
  --source private-approved-source.json ^
  --output private-comparison.json
```

Statuses:

- `MATCH`
- `MISSING_IN_PORTAL`
- `MISSING_IN_SOURCE`
- `VALUE_DIFFERENT`
- `MINOR_VARIATION`
- `CONFLICT`
- `MANUAL_REVIEW`
- `NOT_AVAILABLE`

## Class XI source priority

When Education Profile fields are later wired to the school data layer, use:

1. OFSS — primary admission source
2. e-Shiksha Kosh — secondary source
3. UDISE — current enrollment/status reference
4. Siwan Dropbox — fallback/history/import reference

This priority is for reconciliation and proposed values. It does not authorize destructive synchronization.

## Write-mode design

Future write support must keep four distinct stages:

```text
SCAN -> COMPARE -> PREVIEW -> APPLY -> SUBMIT
```

`APPLY` must fill only explicitly approved fields. `SUBMIT` must require separate explicit authorization and must never be implied by APPLY approval.

At present, the CLI rejects `apply` and `submit` commands on purpose.

## Development notes

- BrowserAct is only the browser-control layer.
- The current module uses only Python standard library plus the external `browser-act` CLI.
- No private values are committed.
- Keep runtime evidence/checkpoints outside Git.
- Update DevOS semantic context when this workflow materially changes.


## Windows GUI

A lightweight Tkinter GUI is available:

```text
browser-portal-automation/udise/student-profile/gui.py
browser-portal-automation/udise/student-profile/run_gui.bat
```

On Windows, double-click:

```text
run_gui.bat
```

or run:

```powershell
python browser-portal-automation/udise/student-profile/gui.py
```

GUI flow:

1. Complete UDISE login/CAPTCHA/OTP manually in the BrowserAct-controlled Chrome session.
2. Keep the default session name `udise-profile` or enter the session you are using.
3. Click **Check Connection**.
4. Enter a test student label.
5. Click **Start GP/EP/FP Discovery**.
6. A console window opens for the interactive BrowserAct state-index prompts.
7. Use **Open Runtime Folder** to inspect captured evidence/checkpoints.
8. Use **Compare Portal vs Source** and **Create Preview** for read-only review.

`APPLY` and `SUBMIT` remain visibly disabled in the GUI until live portal selectors and explicit write approval gates are implemented.
