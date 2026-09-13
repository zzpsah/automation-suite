# Project State — Windows AI Work Browser

## Goal
Build a Windows-first, full-fledged Chromium browser that feels familiar to Chrome users while adding a powerful local AI work/automation layer.

## Repository
`zzpsah/automation-suite`

## Working branch
`browser-automation/windows-work-browser`

## Architecture decision
- Browser foundation: BrowserOS/Chromium is the leading candidate.
- Web automation: Playwright-compatible execution.
- Desktop automation: AutoHotkey + Windows APIs.
- External AI control: MCP gateway.
- Agent loop: observe → plan → act → verify → recover.
- Product remains useful as a normal browser without AI.

## Required feature groups
- Browser: tabs, windows, profiles, extensions, bookmarks, history, downloads, printing, DevTools.
- AI: multi-provider agent hub, task execution, extraction, verification, recovery.
- Desktop: AHK/WinAPI, clipboard, native dialogs, windows, printer, approved native apps.
- PDF: viewer, OCR, merge, split, reorder, compress, annotate, sign, print, generate.
- Files: local explorer, FTP/SFTP/WebDAV/cloud connectors.
- Images: photo/signature crop, deskew, background removal, resize/compress/format conversion.
- Communications: Telegram/email and future supported connectors.
- Workflows: record/replay, scheduling, resumable jobs, checkpoints, audit/evidence.
- Vault: Windows-protected local credentials; AI cannot reveal raw secrets.

## Safety boundary
No unrestricted model-generated shell/AHK execution. Every automation action is validated and policy checked before execution.

## Immediate next engineering phases
1. Inspect BrowserOS build system and Chromium patch boundary.
2. Inspect open-browser-use MCP/SDK boundary.
3. Inspect browser-use agent primitives.
4. Review licenses and provenance for all upstream sources.
5. Produce a reproducible Windows build plan.
6. Implement a minimal browser + MCP + Playwright vertical slice.
7. Add desktop adapter and verify a browser→native-dialog workflow.
8. Add file/PDF/image services.
9. Add workflow engine and recovery/checkpointing.
10. Build signed/reproducible Windows packaging and CI.
