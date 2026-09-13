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
- Close tabs with **× Tab** and confirm closing the last tab creates a usable home tab rather than leaving a broken shell.

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
- Click **Test Portal** and confirm the packaged synthetic portal opens in the active DEVOS tab.
- Run `read #status` and confirm `ready` is returned in the command status area.
- Run `click #next` and confirm the visible page advances.
- Run `wait for #detail` and confirm success.
- Run a bounded sequence such as `click #next; wait for #students; read #status` and confirm steps execute in order.
- Enter an unsupported command and confirm it fails visibly instead of pretending to execute.

## 6. Approval boundary
- Run a `submit <selector>` command against a harmless synthetic control if one is prepared for the test.
- Confirm a blocking approval prompt appears before the click is executed.
- Choose **No** and confirm the action does not execute.
- Repeat and choose **Yes** only on a synthetic fixture; confirm the approved action executes.
- For an interrupted committing task, confirm recovery asks for a fresh approval rather than silently reusing the old one.

## 7. Synthetic portal v0.1 acceptance
- Run `process synthetic portal`.
- If the synthetic portal is not already open, confirm DEVOS loads the packaged fixture automatically.
- Confirm the workflow processes 100 records in the same visible DEVOS browser/session.
- Confirm completion reports an export under `Downloads/DEVOS/SyntheticPortalExport`.
- Confirm both `students.json` and `students.csv` exist and contain 100 records.

Automated CI regression already proves the workflow can stop after record 47 and a fresh workflow resumes with record 48 through record 100, without reprocessing records 1-47. On a real desktop, optionally interrupt the app during this workflow, relaunch it, run `process synthetic portal` again and confirm the status reports a recovery checkpoint before continuing.

## 8. Generic task recovery
- Run a harmless multi-step command sequence.
- Interrupt before all steps finish only on the synthetic fixture.
- Relaunch DEVOS.
- Confirm the interrupted task is detected and the user is offered Resume/Cancel.
- Confirm cancelling removes the pending task.
- Confirm resuming continues from its checkpoint rather than replaying already completed steps.

## Acceptance result
Record:
- Windows version:
- Artifact digest:
- Launch: PASS/FAIL
- Navigation/tab open+close: PASS/FAIL
- Session/profile: PASS/FAIL
- Downloads: PASS/FAIL
- Command bar/multi-step: PASS/FAIL
- Approval boundary: PASS/FAIL
- Synthetic 100-record crawl/export: PASS/FAIL
- Recovery: PASS/FAIL
- Notes / defects:

Do not mark PR #16 ready to merge until all required interactive checks pass or any exception is explicitly documented and accepted.
