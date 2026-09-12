# DEVOS Scan — Phase 1 Status

Last documented revision: `cc2665da64ec32c2d685885dc566ba31dcf2d477`

## Delivered

| Capability | Status | Evidence / notes |
|---|---|---|
| Kotlin Android project | Implemented | Gradle Kotlin DSL project under `android-document-scanner/` |
| Jetpack Compose UI | Implemented | Premium dark scanner/review/editor flow |
| CameraX capture | Implemented | Back camera + quality capture mode |
| Camera permission | Implemented | Runtime permission screen/request |
| Automatic document detection | Implemented | Post-capture OpenCV contour/quad detection |
| Perspective correction | Implemented | Four-point OpenCV perspective warp |
| Manual corner adjustment UI | Implemented | Four draggable corner handles |
| Original filter | Implemented | Preserves page bitmap |
| Auto enhancement | Implemented | CLAHE-based local contrast enhancement |
| Mono filter | Implemented | Grayscale |
| B&W filter | Implemented | Adaptive threshold |
| Batch scanning | Implemented | Multiple pages held in current session |
| Page review | Implemented | Main preview + thumbnails + selection |
| PDF export | Implemented | Android `PdfDocument`, currently to cache |
| OCR architecture | Implemented | `OcrEngine` provider boundary; no fake OCR |
| CI build | Implemented | GitHub Actions debug/release build workflow |
| Unit-test execution | Configured | Must be confirmed by successful CI run |
| Device/emulator test | Not yet verified | Requires actual Android device/emulator |
| Live document overlay | Phase 2 | Current detector runs after capture |
| Automatic shutter | Phase 2 | Not implemented |
| Persistent sessions | Phase 2 | Current batch is in-memory |
| SAF Save As/share | Phase 2 | Current PDF is written to app cache |
| Real OCR provider | Phase 2 | Interface exists; provider not selected |

## Build verification history

### Run #1
- Workflow: `Android Document Scanner Build`
- Run: `34713455738`
- Commit: `daed804cbd66e4aebfcde2d905491ed98c97d65a`
- Result: failed during Kotlin compilation.
- Confirmed issue included a missing Compose `Image` import.

### Run #2
- Workflow: `Android Document Scanner Build`
- Run: `34713732903`
- Commit: `c77d7765b032e66362eacf3a85c128e17b8ccaba`
- Purpose: verify the Compose `Image` import fix and continue build/test/APK generation.
- At the time this document was written, the build job was still in progress at the APK build step. Do not mark Phase 1 build-ready until the run completes successfully.

## Readiness gates

Phase 1 is considered **release-ready only when all are true**:

1. CI debug APK build succeeds.
2. CI release APK build succeeds.
3. Unit tests pass.
4. APK artifact is actually uploaded by CI.
5. APK artifact can be downloaded and inspected.
6. A real-device/emulator smoke test has been performed, or the limitation is explicitly documented.
7. No known compile/runtime blocker remains.

## Product truth rules

- Never call a feature complete merely because a UI control exists.
- Never claim OCR output without a real OCR provider.
- Never claim device testing when only CI/unit tests were run.
- Keep implementation, verification and planned work clearly separated.
- Record significant architectural changes in `CHANGELOG.md`.
