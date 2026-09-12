# Windows Work Browser — Requirements

## Product identity
A full-fledged Chromium browser for Windows that feels like a clean Chrome/ChromeOS-style workspace while adding a powerful local automation layer. Normal browsing must remain first-class; desktop automation is an optional capability.

## Core requirements
- Chromium-class browsing, tabs, windows, profiles, bookmarks, history, downloads, extensions, DevTools, printing and PDF.
- AI Agent modes: Browse, Assist, Automate.
- Browser automation through Playwright-compatible control and/or open-browser-use integration.
- Desktop automation through AutoHotkey + Windows APIs, with validated action schemas rather than unrestricted AI-generated scripts.
- MCP gateway so ChatGPT/Codex/Claude/Gemini-compatible agents can control approved capabilities.
- Human-in-the-loop for OTP/CAPTCHA, payments, destructive actions and final sensitive submissions.
- Universal extraction: HTML/JS tables, paginated records, detail pages, PDFs and repeated forms; CSV/XLSX/JSON/PDF output.
- PDF workspace: view, search, OCR, merge, split, reorder, rotate, compress, annotate, redact, sign, print and generate PDFs.
- Image/photo/signature tools: crop, deskew, background removal, resize, compression, format conversion and exact dimension/file-size validation.
- File workspace: local files, FTP/SFTP/WebDAV/SMB/cloud connectors where supported.
- Communication workspace: Telegram/email and API-backed messaging integrations with permissions.
- Workflow recorder/replay, scheduler, resumable jobs and self-healing/recovery.
- Local-first credential vault protected by Windows security facilities; agents must not expose raw secrets.
- Automation Suite integration without coupling every existing project to the browser.

## External reusable components
Keep reusable upstream integrations/components documented and vendorable under `browser-automation/vendor/` or referenced as pinned submodules/packages where licensing/build constraints permit:
- BrowserOS: Chromium fork + agent platform architecture reference/base candidate.
- open-browser-use: real-browser automation, Chromium MV3 extension, native messaging, MCP, Playwright-shaped SDK; preserve extension source/build recipe so it can be reused for future projects.
- browser-use: agent/browser automation and MCP patterns.
- Noi: UI/workspace and local-first browser ideas.
- AutoHotkey: Windows desktop automation adapter.

Do not blindly merge upstream repositories. Preserve provenance, LICENSE/NOTICE files, pinned revisions, upstream URL, integration purpose, local patches, and upgrade procedure.

## Architecture principle
AI -> intent/plan -> typed action schema -> permission/policy validation -> browser/desktop/file/PDF adapter -> execution -> verification -> evidence/log -> recovery/next action.

## Non-goals
- Do not replace Chromium with a toy embedded webview.
- Do not make desktop automation mandatory for ordinary browsing.
- Do not give the AI unrestricted shell/AHK execution.
- Do not claim a feature is implemented until it has a build/test/evidence path.

## Acceptance criteria
1. Windows build launches a real Chromium browser.
2. Normal browsing works independently of the agent.
3. Agent can perform a verified browser task.
4. Agent can perform an approved Windows desktop action through the adapter.
5. MCP can expose only policy-approved capabilities.
6. A workflow can be recorded, replayed, paused, resumed and verified.
7. Upstream components can be reused in another project using documented provenance and build instructions.
8. CI records build/test results and artifacts.
