# Session — 2026-09-18 — UDISE Student Profile GUI

Added a lightweight Windows Tkinter GUI for the merged UDISE individual Student Profile automation.

## Added
- `browser-portal-automation/udise/student-profile/gui.py`
- `browser-portal-automation/udise/student-profile/run_gui.bat`
- GUI import smoke test
- README usage instructions

## GUI actions
- Check BrowserAct connection/session.
- Start interactive one-student GP/EP/FP discovery in a separate console.
- Compare portal snapshot vs approved source JSON.
- Create no-write preview.
- Open private runtime evidence/checkpoint folder.
- APPLY and SUBMIT remain disabled.

## Safety
Authentication/security challenges stay manual. No security bypass, credential storage, or production deployment was added.
