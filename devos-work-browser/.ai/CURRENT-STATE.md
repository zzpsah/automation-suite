# Current State

Status: DEVOS Work Browser core v0.1 is code-complete and machine-verified end to end on `feat/devos-work-browser-core`.

## Verified core evidence
- F0 custom Windows shell uses .NET 8 WPF + Microsoft WebView2.
- F1 browser core includes open/close tabs, shared persistent WebView2 profile, DEVOS download directory, and session save/restore.
- F2 same-browser WebView2 automation adapter supports click/type/read/wait primitives in the active visible tab.
- F3 deterministic action executor performs verification and bounded retry.
- F4 table extraction parser and CSV serialization are implemented.
- F5 command execution is wired through checkpointed task runtime; active tasks persist locally and interrupted tasks can resume after restart. Committing interrupted tasks require a fresh recovery approval.
- F6 constrained human-language planner emits structured browser actions and supports semicolon-separated bounded sequences.
- F7 approval policy requires explicit approval for committing command categories.
- The browser shell exposes a DEVOS command bar, `Ctrl+Space` focus, visible status/output and approval prompts.
- The packaged **Test Portal** fixture contains 100 synthetic student records.
- `process synthetic portal` runs a real adapter-driven workflow: open/read each record, checkpoint after every record, resume from the saved record, and export JSON + CSV.
- The packaged EXE exposes an isolated `--self-test` mode using a temporary DEVOS state/profile root so automated acceptance does not depend on or mutate ordinary browser task state.
- Stable WPF `AutomationProperties.AutomationId` values are defined for the release-critical shell controls and are exercised by WinApp UI.

## Packaged browser and desktop-UI acceptance
WinApp/UI verification run `34807032368` on head `bc010bf97c27fbf95963219c19985a7c5d9458df` completed successfully.
- Microsoft WinApp CLI setup and CLI verification: success (`0.6.0` on the runner).
- Restore, build and all 18 unit/regression tests: success.
- Self-contained `win-x64` publish: success.
- Packaged synthetic portal presence check: success.
- Packaged end-to-end WebView2 browser self-test: success.
- The packaged self-test verified real adapter click/read behavior, processed records 1-47, persisted the 47→48 checkpoint boundary, resumed at 48 with a fresh workflow instance, completed through 100, and verified 100-record JSON + CSV exports.
- WinApp UI desktop acceptance: success.
- WinApp UI verified the stable shell AutomationIds, invoked New Tab and Close Tab, invoked the bundled Test Portal button, set and ran `read #status` through the visible command bar, observed the expected `ready` result, opened the blocking approval dialog with `submit #next`, declined it, and observed the visible `Approval declined` status.
- UI automation evidence was uploaded as `DEVOS-Work-Browser-WinAppUI`, artifact id `10333143280`, digest `sha256:4215831898dcc568de28c1975ca7b768a49bc31d300573353225fada427ca6ae`.
- The WinApp UI artifact contains the UI tree, launch/test-portal/approval/final screenshots, and the acceptance summary.
- Normal packaged EXE startup smoke: success.
- Windows package artifact: `DEVOS-Work-Browser-win-x64`, artifact id `10333840824`, size `72304466` bytes, digest `sha256:ca0514f0dffe9e7ceda7b6e08657c9be088debef87ead4d3d8fcf3e1f91f8b91`.

## Remaining acceptance boundary
The v0.1 core is machine-verified both at the internal browser/runtime layer and at the outer Windows UI Automation layer. The only remaining non-automated boundary is subjective human UX review on a real Windows desktop: visual polish, perceived responsiveness, ergonomics, and preference-level design feedback. CI/WinApp UI must not be represented as a substitute for that subjective human review.

## Safety / scope
- `main` remains untouched by this work.
- No live portal credentials or production mutations were used.
- PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, workflow recorder and complex desktop automation remain deferred feature layers.
