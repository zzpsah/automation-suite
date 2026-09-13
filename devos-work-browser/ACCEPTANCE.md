# DEVOS Work Browser — Interactive Windows Acceptance

Run this checklist on a real Windows desktop before merge/release. CI/package/startup-smoke success is necessary but is not a substitute for this visual and interaction pass.

## 1. Launch
- Download/extract `DEVOS-Work-Browser-win-x64`.
- Start `DEVOS.WorkBrowser.exe`.
- Confirm the window opens without an error dialog.
- Confirm an embedded page renders and the app remains responsive.

## 2. Browser fundamentals
- Navigate to a normal HTTPS page from the address bar.
- Enter plain natural-language text in the address bar and confirm it becomes a web search.
- Verify Back, Forward, Reload and Home.
- Open at least three tabs and switch between them.

## 3. Session/profile persistence
- Leave multiple tabs open, close the app normally, then reopen it.
- Confirm tab URLs and selected-tab position restore sensibly.
- Confirm normal WebView2 profile/session behavior persists across restart.

## 4. Downloads
- Trigger a harmless test download.
- Confirm it is saved under the user's `Downloads/DEVOS` directory.
- Confirm the browser remains responsive after download completion.

## 5. DEVOS command bar
- Press `Ctrl+Space` and confirm focus moves to the DEVOS command box.
- On the synthetic portal, run `read #status` and confirm the visible result is returned in the command status area.
- Run `click #next` and confirm the active page advances.
- Run `wait for #detail` and confirm success.
- Run a valid `type <value> into <selector>` command on a harmless text input when available.
- Enter an unsupported command and confirm it fails visibly instead of pretending to execute.

## 6. Approval boundary
- Run a `submit <selector>` command against a harmless synthetic control.
- Confirm a blocking approval prompt appears before the click is executed.
- Choose **No** and confirm the action does not execute.
- Repeat and choose **Yes** only on the synthetic fixture; confirm the approved action executes.

## 7. Synthetic portal same-browser control
Use `test-portal/index.html` from this repository as the controlled fixture.

Verify:
- `read #status` initially returns `ready`.
- `click #next` changes the page indicator from page 1 to page 2.
- `click button.open` opens the first visible record.
- `read #detail` returns the selected synthetic record details.
- Browser automation acts inside the same visible DEVOS tab/session; it must not launch a separate Chrome/Edge window.

## 8. Recovery evidence
The automated regression already verifies a 100-step task can resume from checkpoint 47 without replaying steps 1-47. On desktop, additionally confirm closing and reopening the browser does not destroy ordinary tab/session state.

## Acceptance result
Record:
- Windows version:
- Artifact digest:
- Launch: PASS/FAIL
- Navigation/tabs: PASS/FAIL
- Session/profile: PASS/FAIL
- Downloads: PASS/FAIL
- Command bar: PASS/FAIL
- Approval boundary: PASS/FAIL
- Synthetic portal automation: PASS/FAIL
- Notes / defects:

Do not mark PR #16 ready to merge until all required interactive checks pass or any exception is explicitly documented and accepted.
