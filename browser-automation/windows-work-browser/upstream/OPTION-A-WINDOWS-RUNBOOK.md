# Option A Windows Runbook

1. Select the pinned artifact from `OPTION-A-RELEASE.json`.
2. Download to a staging directory; never execute an unverified download.
3. Verify SHA-256 and Authenticode signature.
4. Install into an isolated target and capture the installed executable hash/version.
5. Launch and verify HTTPS navigation, new tab/window, profile persistence and browser-control availability.
6. Deploy the Work Browser overlay through supported extension/MCP/native-messaging/service interfaces.
7. Run read-only smoke tests first; writes require policy approval.
8. Capture evidence and promote only after all gates pass.

Rollback: retain the last verified artifact; on failure restore it and preserve evidence. Never silently retry sensitive or destructive actions.

Promotion states:
`DISCOVERED → STAGED → VERIFIED → INSTALLED → SMOKE-PASSED → OVERLAY-PASSED → CANDIDATE`
