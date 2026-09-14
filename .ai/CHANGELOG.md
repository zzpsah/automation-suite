## 2026-09-14 — fix: harden UMVInputBot delivery progress update
- Commit: aa7a247b18cab4ae00a3fc8188dfa22e47363fba
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/telegram_delivery_progress.py`

## 2026-09-14 — Use UMVInputBot token for progress-message edits
- Commit: f9e6b3922d2c7bd488313cb09159f2b51076e00c
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/global-document-telegram-notifier.yml`

## 2026-09-14 — Fix Stage 10 progress updater to edit UMVInputBot message
- Commit: 90aa0004d67d8ff006d12d6bf38a3fde043229fe
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/telegram_delivery_progress.py`

## 2026-09-14 — feat: update Telegram progress after eLetters delivery
- Commit: e77ab320a5fdfcaebcec0c3f0d09c6b6e7cf0b35
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/global-document-telegram-notifier.yml`

## 2026-09-14 — docs: document Stage 10 eLetters durable delivery
- Commit: cbdd3cd30ac35011b419141ed81e98728d2d9211
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `docs/STAGE_10_ELETTERS_DURABLE_DELIVERY.md`

## 2026-09-14 — feat: align targeted eLettersBot delivery with Stage 10 state machine
- Commit: caf61a729a5729e7f8580255878047376179990d
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/telegram_publication_notifier_targeted.py`

## 2026-09-14 — feat: harden eLettersBot durable delivery
- Commit: 64a9fd1174fd3ed2beb3a46f0e8a20844932f814
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/telegram_publication_notifier_v3.py`

## 2026-09-14 — feat: add atomic eLettersBot delivery claim
- Commit: 6f7bae428f909d6298005323ce31e34f216ee860
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `school-document-pipeline/supabase/migrations/20260914103100_eletters_delivery_claim.sql`

## 2026-09-14 — feat: add durable eLettersBot delivery state table
- Commit: 7eda4c91227c5cd2bee939ad0bb6b559d2fe4ae2
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `school-document-pipeline/supabase/migrations/20260914103000_eletters_delivery_state.sql`

## 2026-09-14 — Document permanent scanner beta quality gate
- Commit: 70baceb59deb71f760d40ffa9e9b07dd8261d2ba
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/README.md`

## 2026-09-14 — Strengthen scanner build smoke test
- Commit: ae6c7309200d5e6e34c6f996282424bc41332815
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/android-document-scanner-build.yml`

## 2026-09-14 — Add Android emulator install smoke test
- Commit: 377d0bdd9bc26346bff1dc23b91e9b944d16ee09
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/android-document-scanner-build.yml`

## 2026-09-14 — Fix AndroidView scanner camera binding
- Commit: 9489b74a8a6da741d5e52971c851de2901dec0ec
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/MainActivity.kt`

## 2026-09-14 — Fix scanner image processor angle calculation
- Commit: 1721d324ba2225eb010491ac85426cf5c0154685
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/ImageProcessor.kt`

## 2026-09-14 — Trigger scanner verification on completed implementation
- Commit: 2cba7bd1184bd21b779faabf10df67ac28b86720
- Author: PRASHANT KUMAR SAH
- Classification: routine
- Changed files:
- (no application files detected)

## 2026-09-14 — Complete scanner capture, review, editing, persistence and export flow
- Commit: adb940f60cbad811fe1aa5f27750e38102b59706
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/MainActivity.kt`

## 2026-09-14 — Add durable local scan session storage
- Commit: ae945d08d0c2b9c05adb165fa90454c9f986fc2f
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/ScanSessionStore.kt`

## 2026-09-14 — Add secure PDF sharing provider
- Commit: 8ed3e77afcf2f016e31797e7052728b460176f29
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/AndroidManifest.xml`

## 2026-09-14 — chore(devos): record Work Browser prototype retirement
- Commit: aa9a782ea5c62d04f8277e5da75614e713d83a91
- Author: PRASHANT KUMAR SAH
- Classification: routine
- Changed files:
- (no application files detected)

## 2026-09-14 — chore: remove failed Windows Work Browser prototype
- Commit: 9b403ac919155d414d5ba53692fbea9abb093a06
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/windows-work-browser-agent-ci.yml`
- `.github/workflows/windows-work-browser-build.yml`
- `.github/workflows/windows-work-browser-contract.yml`
- `.github/workflows/windows-work-browser-option-a.yml`
- `.github/workflows/windows-work-browser-release-gate.yml`
- `.github/workflows/windows-work-browser-release.yml`
- `browser-automation/.ai/PROJECT_STATE.md`
- `browser-automation/README.md`
- `browser-automation/docs/ARCHITECTURE.md`
- `browser-automation/docs/REQUIREMENTS.md`
- `browser-automation/docs/UPSTREAM-COMPONENTS.md`
- `browser-automation/vendor/README.md`
- `browser-automation/windows-work-browser/.ai/PROJECT-CONTEXT.md`
- `browser-automation/windows-work-browser/.github/workflows/agent-package-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/contract-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/product-contract-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/windows-build-lane.yml`
- `browser-automation/windows-work-browser/BUILD-STATUS.md`
- `browser-automation/windows-work-browser/DEVELOPER-RELEASE.md`
- `browser-automation/windows-work-browser/README.md`
- `browser-automation/windows-work-browser/RELEASE-READINESS.json`
- `browser-automation/windows-work-browser/agent/action-contract.ts`
- `browser-automation/windows-work-browser/agent/browser-control-contract.ts`
- `browser-automation/windows-work-browser/agent/credential-vault-contract.ts`
- `browser-automation/windows-work-browser/agent/evidence-schema.ts`
- `browser-automation/windows-work-browser/agent/executor-contract.test.ts`
- `browser-automation/windows-work-browser/agent/executor-contract.ts`
- `browser-automation/windows-work-browser/agent/extraction-contract.ts`
- `browser-automation/windows-work-browser/agent/mcp-gateway-contract.ts`
- `browser-automation/windows-work-browser/agent/native-executor-contract.ts`
- `browser-automation/windows-work-browser/agent/orchestrator.md`
- `browser-automation/windows-work-browser/agent/permission-contract.ts`
- `browser-automation/windows-work-browser/agent/permission-policy.ts`
- `browser-automation/windows-work-browser/agent/policy-engine.ts`
- `browser-automation/windows-work-browser/agent/task-contract.ts`
- `browser-automation/windows-work-browser/agent/task-runner.ts`
- `browser-automation/windows-work-browser/agent/task-state.ts`
- `browser-automation/windows-work-browser/agent/update-contract.ts`
- `browser-automation/windows-work-browser/agent/verification-contract.ts`
- `browser-automation/windows-work-browser/agent/windows-native-contract.ts`
- `browser-automation/windows-work-browser/agent/work-tools-contract.ts`
- `browser-automation/windows-work-browser/agent/workflow-contract.ts`
- `browser-automation/windows-work-browser/docs/BUILD-PLAN.md`
- `browser-automation/windows-work-browser/docs/CI-CONTRACT.md`
- `browser-automation/windows-work-browser/docs/COMPOSITION-MATRIX.md`
- `browser-automation/windows-work-browser/docs/FINAL-RELEASE-PACKAGE.md`
- `browser-automation/windows-work-browser/docs/IMPLEMENTATION-MATRIX.md`
- `browser-automation/windows-work-browser/docs/RELEASE-CHECKLIST.md`
- `browser-automation/windows-work-browser/docs/RELEASE-GATES.md`
- `browser-automation/windows-work-browser/docs/RELEASE-READINESS.json`
- `browser-automation/windows-work-browser/docs/TEST-MODE.md`
- `browser-automation/windows-work-browser/docs/THIRD-PARTY-NOTICES.md`
- `browser-automation/windows-work-browser/docs/UPSTREAM-LOCK.md`
- `browser-automation/windows-work-browser/docs/UPSTREAM-RESEARCH-2026-09.md`
- `browser-automation/windows-work-browser/docs/WINDOWS-BUILD-BOOTSTRAP.md`
- `browser-automation/windows-work-browser/docs/WINDOWS-BUILD-LANES.md`
- `browser-automation/windows-work-browser/extension/background.js`
- `browser-automation/windows-work-browser/extension/devos-overlay.js`
- `browser-automation/windows-work-browser/extension/manifest.json`
- `browser-automation/windows-work-browser/extension/sidepanel.html`
- `browser-automation/windows-work-browser/extension/sidepanel.js`
- `browser-automation/windows-work-browser/extension/styles.css`
- `browser-automation/windows-work-browser/package.json`
- `browser-automation/windows-work-browser/runtime/automation-runtime.ts`
- `browser-automation/windows-work-browser/runtime/browser-control.ts`
- `browser-automation/windows-work-browser/runtime/capability-catalog.json`
- `browser-automation/windows-work-browser/runtime/capability-registry.test.ts`
- `browser-automation/windows-work-browser/runtime/capability-registry.ts`
- `browser-automation/windows-work-browser/runtime/capability-services.ts`
- `browser-automation/windows-work-browser/runtime/cdp-adapter.ts`
- `browser-automation/windows-work-browser/runtime/communication-service.test.ts`
- `browser-automation/windows-work-browser/runtime/communication-service.ts`
- `browser-automation/windows-work-browser/runtime/desktop-control.ts`
- `browser-automation/windows-work-browser/runtime/example-workflows.json`
- `browser-automation/windows-work-browser/runtime/extraction-engine.test.ts`
- `browser-automation/windows-work-browser/runtime/extraction-engine.ts`
- `browser-automation/windows-work-browser/runtime/extraction-planner.ts`
- `browser-automation/windows-work-browser/runtime/image-service.test.ts`
- `browser-automation/windows-work-browser/runtime/image-service.ts`
- `browser-automation/windows-work-browser/runtime/json-checkpoint-store.test.ts`
- `browser-automation/windows-work-browser/runtime/json-checkpoint-store.ts`
- `browser-automation/windows-work-browser/runtime/local-agent-server.test.ts`
- `browser-automation/windows-work-browser/runtime/local-agent-server.ts`
- `browser-automation/windows-work-browser/runtime/local-file-service.test.ts`
- `browser-automation/windows-work-browser/runtime/local-file-service.ts`
- `browser-automation/windows-work-browser/runtime/local-task-queue.ts`
- `browser-automation/windows-work-browser/runtime/mcp-gateway.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-gateway.ts`
- `browser-automation/windows-work-browser/runtime/mcp-runtime-bridge.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-process.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-server.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-server.ts`
- `browser-automation/windows-work-browser/runtime/orchestration.smoke.test.ts`
- `browser-automation/windows-work-browser/runtime/pdf-service.test.ts`
- `browser-automation/windows-work-browser/runtime/pdf-service.ts`
- `browser-automation/windows-work-browser/runtime/playwright-adapter.ts`
- `browser-automation/windows-work-browser/runtime/playwright-controller.ts`
- `browser-automation/windows-work-browser/runtime/playwright-e2e.ts`
- `browser-automation/windows-work-browser/runtime/policy-engine.test.ts`
- `browser-automation/windows-work-browser/runtime/protected-file-vault.ts`
- `browser-automation/windows-work-browser/runtime/release-component-integration.test.ts`
- `browser-automation/windows-work-browser/runtime/remote-file-services.ts`
- `browser-automation/windows-work-browser/runtime/service-security.test.ts`
- `browser-automation/windows-work-browser/runtime/smb-file-service.ts`
- `browser-automation/windows-work-browser/runtime/ssh2-sftp-client.d.ts`
- `browser-automation/windows-work-browser/runtime/test-mode.ts`
- `browser-automation/windows-work-browser/runtime/update-manager.test.ts`
- `browser-automation/windows-work-browser/runtime/update-manager.ts`
- `browser-automation/windows-work-browser/runtime/windows-credential-vault.test.ts`
- `browser-automation/windows-work-browser/runtime/windows-credential-vault.ts`
- `browser-automation/windows-work-browser/runtime/windows-dpapi-vault.ts`
- `browser-automation/windows-work-browser/runtime/windows-native-e2e.ts`
- `browser-automation/windows-work-browser/runtime/windows-native-executor.ts`
- `browser-automation/windows-work-browser/runtime/work-tools.test.ts`
- `browser-automation/windows-work-browser/runtime/workflow-service.test.ts`
- `browser-automation/windows-work-browser/runtime/workflow-service.ts`
- `browser-automation/windows-work-browser/runtime/workspace-contract.ts`
- `browser-automation/windows-work-browser/scripts/Start-Work-Browser.cmd`
- `browser-automation/windows-work-browser/scripts/generate-sbom.mjs`
- `browser-automation/windows-work-browser/scripts/release-preflight.mjs`
- `browser-automation/windows-work-browser/scripts/run-work-browser-test.ps1`
- `browser-automation/windows-work-browser/scripts/start-work-browser.ps1`
- `browser-automation/windows-work-browser/scripts/validate-release-readiness.mjs`
- `browser-automation/windows-work-browser/tsconfig.json`
- `browser-automation/windows-work-browser/upstream/BROWSEROS-PIN.md`
- `browser-automation/windows-work-browser/upstream/BUILD-GATE.md`
- `browser-automation/windows-work-browser/upstream/OPTION-A-ARTIFACT-LANE.md`
- `browser-automation/windows-work-browser/upstream/OPTION-A-ARTIFACT-MANIFEST.schema.json`
- `browser-automation/windows-work-browser/upstream/OPTION-A-RELEASE.json`
- `browser-automation/windows-work-browser/upstream/OPTION-A-WINDOWS-RUNBOOK.md`
- `browser-automation/windows-work-browser/upstream/REUSE-MATRIX.md`
- `browser-automation/windows-work-browser/upstream/bootstrap-windows.ps1`
- `browser-automation/windows-work-browser/upstream/option-a-bootstrap.ps1`
- `browser-automation/windows-work-browser/upstream/option-a-overlay-bootstrap.ps1`

## 2026-09-13 — fix(scanner): apply flash changes without camera rebind
- Commit: aae30b1652e681831dde8f94ba5ace4870a62652
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/MainActivity.kt`

## 2026-09-13 — feat(scanner): improve editor rewarp and camera flash
- Commit: 99f39cb58a749f2fe1120d9a53171b1c24b2caff
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/MainActivity.kt`

## 2026-09-13 — feat(scanner): preserve source image for true corner rewarp
- Commit: f008d4f07ddcd30051e0336bba257c7944fe19e6
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `android-document-scanner/app/src/main/java/com/devos/docscanner/ScannerModels.kt`

## 2026-09-13 — chore(browser): remove duplicate overlay entrypoint
- Commit: 4c4db9453cac9080bb43cada5deff940bd6ce416
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `browser-automation/windows-work-browser/extension/content.js`

## 2026-09-13 — feat(browser): open DEVOS agent from page launcher
- Commit: 90533555098969229c8fdaf3aa5fac7c9c41d062
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `browser-automation/windows-work-browser/extension/background.js`

## 2026-09-13 — feat(browser): add visible DEVOS AI page launcher
- Commit: 03d5c098861096637006a6b908f0c044d8f58742
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `browser-automation/windows-work-browser/extension/content.js`

## 2026-09-13 — feat(browser): expose visible DEVOS AI overlay on webpages
- Commit: 0cec7db3a698d02cccb2eccd3e044a643e94196b
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `browser-automation/windows-work-browser/extension/manifest.json`

## 2026-09-13 — feat: add Windows Work Browser developer preview
- Commit: 27bb7f01166bd34024b89342bddde4ce0f95d5fe
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/windows-work-browser-agent-ci.yml`
- `.github/workflows/windows-work-browser-build.yml`
- `.github/workflows/windows-work-browser-contract.yml`
- `.github/workflows/windows-work-browser-option-a.yml`
- `.github/workflows/windows-work-browser-release-gate.yml`
- `.github/workflows/windows-work-browser-release.yml`
- `browser-automation/.ai/PROJECT_STATE.md`
- `browser-automation/README.md`
- `browser-automation/docs/ARCHITECTURE.md`
- `browser-automation/docs/REQUIREMENTS.md`
- `browser-automation/docs/UPSTREAM-COMPONENTS.md`
- `browser-automation/vendor/README.md`
- `browser-automation/windows-work-browser/.ai/PROJECT-CONTEXT.md`
- `browser-automation/windows-work-browser/.github/workflows/agent-package-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/contract-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/product-contract-ci.yml`
- `browser-automation/windows-work-browser/.github/workflows/windows-build-lane.yml`
- `browser-automation/windows-work-browser/BUILD-STATUS.md`
- `browser-automation/windows-work-browser/DEVELOPER-RELEASE.md`
- `browser-automation/windows-work-browser/README.md`
- `browser-automation/windows-work-browser/RELEASE-READINESS.json`
- `browser-automation/windows-work-browser/agent/action-contract.ts`
- `browser-automation/windows-work-browser/agent/browser-control-contract.ts`
- `browser-automation/windows-work-browser/agent/credential-vault-contract.ts`
- `browser-automation/windows-work-browser/agent/evidence-schema.ts`
- `browser-automation/windows-work-browser/agent/executor-contract.test.ts`
- `browser-automation/windows-work-browser/agent/executor-contract.ts`
- `browser-automation/windows-work-browser/agent/extraction-contract.ts`
- `browser-automation/windows-work-browser/agent/mcp-gateway-contract.ts`
- `browser-automation/windows-work-browser/agent/native-executor-contract.ts`
- `browser-automation/windows-work-browser/agent/orchestrator.md`
- `browser-automation/windows-work-browser/agent/permission-contract.ts`
- `browser-automation/windows-work-browser/agent/permission-policy.ts`
- `browser-automation/windows-work-browser/agent/policy-engine.ts`
- `browser-automation/windows-work-browser/agent/task-contract.ts`
- `browser-automation/windows-work-browser/agent/task-runner.ts`
- `browser-automation/windows-work-browser/agent/task-state.ts`
- `browser-automation/windows-work-browser/agent/update-contract.ts`
- `browser-automation/windows-work-browser/agent/verification-contract.ts`
- `browser-automation/windows-work-browser/agent/windows-native-contract.ts`
- `browser-automation/windows-work-browser/agent/work-tools-contract.ts`
- `browser-automation/windows-work-browser/agent/workflow-contract.ts`
- `browser-automation/windows-work-browser/docs/BUILD-PLAN.md`
- `browser-automation/windows-work-browser/docs/CI-CONTRACT.md`
- `browser-automation/windows-work-browser/docs/COMPOSITION-MATRIX.md`
- `browser-automation/windows-work-browser/docs/FINAL-RELEASE-PACKAGE.md`
- `browser-automation/windows-work-browser/docs/IMPLEMENTATION-MATRIX.md`
- `browser-automation/windows-work-browser/docs/RELEASE-CHECKLIST.md`
- `browser-automation/windows-work-browser/docs/RELEASE-GATES.md`
- `browser-automation/windows-work-browser/docs/RELEASE-READINESS.json`
- `browser-automation/windows-work-browser/docs/TEST-MODE.md`
- `browser-automation/windows-work-browser/docs/THIRD-PARTY-NOTICES.md`
- `browser-automation/windows-work-browser/docs/UPSTREAM-LOCK.md`
- `browser-automation/windows-work-browser/docs/UPSTREAM-RESEARCH-2026-09.md`
- `browser-automation/windows-work-browser/docs/WINDOWS-BUILD-BOOTSTRAP.md`
- `browser-automation/windows-work-browser/docs/WINDOWS-BUILD-LANES.md`
- `browser-automation/windows-work-browser/extension/background.js`
- `browser-automation/windows-work-browser/extension/manifest.json`
- `browser-automation/windows-work-browser/extension/sidepanel.html`
- `browser-automation/windows-work-browser/extension/sidepanel.js`
- `browser-automation/windows-work-browser/extension/styles.css`
- `browser-automation/windows-work-browser/package.json`
- `browser-automation/windows-work-browser/runtime/automation-runtime.ts`
- `browser-automation/windows-work-browser/runtime/browser-control.ts`
- `browser-automation/windows-work-browser/runtime/capability-catalog.json`
- `browser-automation/windows-work-browser/runtime/capability-registry.test.ts`
- `browser-automation/windows-work-browser/runtime/capability-registry.ts`
- `browser-automation/windows-work-browser/runtime/capability-services.ts`
- `browser-automation/windows-work-browser/runtime/cdp-adapter.ts`
- `browser-automation/windows-work-browser/runtime/communication-service.test.ts`
- `browser-automation/windows-work-browser/runtime/communication-service.ts`
- `browser-automation/windows-work-browser/runtime/desktop-control.ts`
- `browser-automation/windows-work-browser/runtime/example-workflows.json`
- `browser-automation/windows-work-browser/runtime/extraction-engine.test.ts`
- `browser-automation/windows-work-browser/runtime/extraction-engine.ts`
- `browser-automation/windows-work-browser/runtime/extraction-planner.ts`
- `browser-automation/windows-work-browser/runtime/image-service.test.ts`
- `browser-automation/windows-work-browser/runtime/image-service.ts`
- `browser-automation/windows-work-browser/runtime/json-checkpoint-store.test.ts`
- `browser-automation/windows-work-browser/runtime/json-checkpoint-store.ts`
- `browser-automation/windows-work-browser/runtime/local-agent-server.test.ts`
- `browser-automation/windows-work-browser/runtime/local-agent-server.ts`
- `browser-automation/windows-work-browser/runtime/local-file-service.test.ts`
- `browser-automation/windows-work-browser/runtime/local-file-service.ts`
- `browser-automation/windows-work-browser/runtime/local-task-queue.ts`
- `browser-automation/windows-work-browser/runtime/mcp-gateway.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-gateway.ts`
- `browser-automation/windows-work-browser/runtime/mcp-runtime-bridge.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-process.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-server.test.ts`
- `browser-automation/windows-work-browser/runtime/mcp-stdio-server.ts`
- `browser-automation/windows-work-browser/runtime/orchestration.smoke.test.ts`
- `browser-automation/windows-work-browser/runtime/pdf-service.test.ts`
- `browser-automation/windows-work-browser/runtime/pdf-service.ts`
- `browser-automation/windows-work-browser/runtime/playwright-adapter.ts`
- `browser-automation/windows-work-browser/runtime/playwright-controller.ts`
- `browser-automation/windows-work-browser/runtime/playwright-e2e.ts`
- `browser-automation/windows-work-browser/runtime/policy-engine.test.ts`
- `browser-automation/windows-work-browser/runtime/protected-file-vault.ts`
- `browser-automation/windows-work-browser/runtime/release-component-integration.test.ts`
- `browser-automation/windows-work-browser/runtime/remote-file-services.ts`
- `browser-automation/windows-work-browser/runtime/service-security.test.ts`
- `browser-automation/windows-work-browser/runtime/smb-file-service.ts`
- `browser-automation/windows-work-browser/runtime/ssh2-sftp-client.d.ts`
- `browser-automation/windows-work-browser/runtime/test-mode.ts`
- `browser-automation/windows-work-browser/runtime/update-manager.test.ts`
- `browser-automation/windows-work-browser/runtime/update-manager.ts`
- `browser-automation/windows-work-browser/runtime/windows-credential-vault.test.ts`
- `browser-automation/windows-work-browser/runtime/windows-credential-vault.ts`
- `browser-automation/windows-work-browser/runtime/windows-dpapi-vault.ts`
- `browser-automation/windows-work-browser/runtime/windows-native-e2e.ts`
- `browser-automation/windows-work-browser/runtime/windows-native-executor.ts`
- `browser-automation/windows-work-browser/runtime/work-tools.test.ts`
- `browser-automation/windows-work-browser/runtime/workflow-service.test.ts`
- `browser-automation/windows-work-browser/runtime/workflow-service.ts`
- `browser-automation/windows-work-browser/runtime/workspace-contract.ts`
- `browser-automation/windows-work-browser/scripts/Start-Work-Browser.cmd`
- `browser-automation/windows-work-browser/scripts/generate-sbom.mjs`
- `browser-automation/windows-work-browser/scripts/release-preflight.mjs`
- `browser-automation/windows-work-browser/scripts/run-work-browser-test.ps1`
- `browser-automation/windows-work-browser/scripts/start-work-browser.ps1`
- `browser-automation/windows-work-browser/scripts/validate-release-readiness.mjs`
- `browser-automation/windows-work-browser/tsconfig.json`
- `browser-automation/windows-work-browser/upstream/BROWSEROS-PIN.md`
- `browser-automation/windows-work-browser/upstream/BUILD-GATE.md`
- `browser-automation/windows-work-browser/upstream/OPTION-A-ARTIFACT-LANE.md`
- `browser-automation/windows-work-browser/upstream/OPTION-A-ARTIFACT-MANIFEST.schema.json`
- `browser-automation/windows-work-browser/upstream/OPTION-A-RELEASE.json`
- `browser-automation/windows-work-browser/upstream/OPTION-A-WINDOWS-RUNBOOK.md`
- `browser-automation/windows-work-browser/upstream/REUSE-MATRIX.md`
- `browser-automation/windows-work-browser/upstream/bootstrap-windows.ps1`
- `browser-automation/windows-work-browser/upstream/option-a-bootstrap.ps1`
- `browser-automation/windows-work-browser/upstream/option-a-overlay-bootstrap.ps1`

## 2026-09-13 — fix: isolate hardened Telegram watchdog concurrency
- Commit: 929e12d0119668cad4fc7a72372b3c1a1dab768f
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/telegram-input-delivery-watchdog-v2.yml`

## 2026-09-13 — chore: finalize Telegram input watchdog branch state
- Commit: 489d5fa88bda04504085094dedf18b5410d9261f
- Author: PRASHANT KUMAR SAH
- Classification: routine
- Changed files:
- (no application files detected)

## 2026-09-13 — noop: align watchdog after cleanup
- Commit: bd3fc350eef2e8ab2b05cc05ed4c76a0d70b6e20
- Author: PRASHANT KUMAR SAH
- Classification: routine
- Changed files:
- (no application files detected)

## 2026-09-13 — chore: confirm Telegram watchdog file
- Commit: 87b9233dec73ef79ae0c0e509a6e4476ec4cf686
- Author: PRASHANT KUMAR SAH
- Classification: routine
- Changed files:
- (no application files detected)

## 2026-09-13 — docs: document Telegram input delivery watchdog
- Commit: 4a0bdb035d8a8df57f51854041bb324931235989
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `README.md`

## 2026-09-13 — fix: run Telegram watchdog on relevant changes
- Commit: 339178eb10ec3071706bcc0b14d15de882ae06eb
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/telegram-input-delivery-watchdog-v2.yml`

## 2026-09-13 — feat: harden Telegram input delivery watchdog
- Commit: b4e3900ad4282c3cbdc8ac4c46c91b221dde9cdd
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/telegram-input-delivery-watchdog-v2.yml`

## 2026-09-13 — feat: add Telegram input delivery watchdog
- Commit: ecf570a312c1755a027fda0653714681be26de6d
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/telegram-input-delivery-watchdog.yml`

## 2026-09-13 — release: school document pipeline v1.0.0 final e2e verification
- Commit: 6ced64f7ed331b1641024bf77d74d75866419345
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `docs/releases/school-document-pipeline-v1.0.0.md`

## 2026-09-13 — fix notifier unit test contract and offline env
- Commit: d4006183577eaaa4b3fe1c73e1162d0335d4edfd
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/test_telegram_publication_notifier.py`

## 2026-09-13 — fix document processor offline concurrency test
- Commit: 83e2287b3a5b075f49c2f8e812f6e9315f71614e
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/test_govdoc_resilience.py`

## 2026-09-13 — fix notifier CI test environment and pytest execution
- Commit: 44735cb1449084de0a05b7c1455830804876e1fc
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/global-document-telegram-notifier.yml`

## 2026-09-13 — use targeted notifier for document dispatch
- Commit: 7c0577be5c383e4653fbca462f2f84ff2d4684ef
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/global-document-telegram-notifier.yml`

## 2026-09-13 — add targeted autonomous Telegram delivery runner
- Commit: d0c24eae0f11926f359f7abe1162eb7694bd092e
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/telegram_publication_notifier_targeted.py`

## 2026-09-13 — fix notifier repository dispatch targeting
- Commit: 1a761f6b919dcf778e8ca6a88db8107439dc7960
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/global-document-telegram-notifier.yml`

## 2026-09-13 — docs: align runbook with autonomous publication and recovery
- Commit: 93b1bc1c9d8d3deeda2d46a844bbe39eae97f0d1
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/OPERATIONS_RUNBOOK.md`

## 2026-09-13 — feat: remove human publication gate and use autonomous safety checks
- Commit: 371e40898b4f7282a92559c863fe607ba9a09a55
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `global-automation/scripts/document/publication_worker.py`

## 2026-09-13 — chore: onboard DevOS portable project memory
- Commit: 26a02d5b0758168888d75cf3f66103c09fe7762a
- Author: PRASHANT KUMAR SAH
- Classification: meaningful
- Changed files:
- `.github/workflows/context-sync.yml`
- `AGENTS.md`

# DevOS Context Change Log

Automatically maintained by Development OS.

## 2026-09-13 — Portable memory onboarding
- Added repository-level DevOS portable context and automatic synchronization.
- Existing modules, workflows, `.claude/`, and source preserved.

