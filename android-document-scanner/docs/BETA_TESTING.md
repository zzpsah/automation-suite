# DevOS Document Scanner — Beta Testing Gate

## Purpose

An APK is not considered release-ready merely because Gradle compilation succeeds. Every candidate must pass installation, launch, automated UI exploration, and critical workflow checks before it is shared for user testing.

## Release pipeline

`Source → Compile → Unit Tests → APK Signing Verification → Emulator Install → App Launch → Automated Functional Tests → Beta Candidate`

## Required gates

### 1. Build
- `assembleDebug`
- `assembleRelease`
- Unit tests

### 2. APK integrity
- Verify the debug APK with Android `apksigner`.
- Confirm the generated APK exists and is the artifact produced by the same commit under test.

### 3. Android runtime smoke test
GitHub Actions boots an Android API 35 emulator and must:
- install the debug APK with `adb install -r`
- launch `com.devos.docscanner/.MainActivity`
- confirm the application process is alive
- confirm the launcher activity is active

A build that compiles but cannot install or launch is a **failed build candidate**.

### 4. Automated functional beta testing
The project should use two complementary layers:

**Firebase Test Lab / Robo Test**
- Device/API matrix testing
- Fresh install and launch exploration
- Permission handling
- Crash/ANR detection
- Screenshots, logs, and test evidence

**Maestro**
- Deterministic end-to-end journeys against the rendered UI
- Useful for Jetpack Compose workflows without requiring test-only application code

## Critical scanner journey

The beta suite should cover, at minimum:

1. Fresh install
2. Launch app
3. Camera permission
4. Camera screen appears
5. Capture a document
6. Image processing completes
7. Document appears in review
8. Add a second page
9. Open manual adjustment
10. Move document corners
11. Apply Original/Auto/Mono/B&W filters
12. Return to review
13. Save PDF using the Android document picker
14. Share PDF
15. Clear session
16. Relaunch and verify persisted session behavior
17. Check for crash/ANR during the journey

## Test evidence

A future beta candidate should retain:
- Git commit SHA
- workflow run ID
- APK artifact ID
- APK SHA-256
- emulator/device matrix
- test result
- failure logs/screenshots/video when available

## Release rule

**Do not share an APK as a final/beta candidate if any mandatory gate fails.**

A green Gradle build alone is insufficient.

## Future expansion

As scanner features are added, extend the automated gate before exposing the feature to the user. Examples:
- gallery import
- live document detection
- automatic capture
- low-light enhancement
- OCR extraction and editable fields
- BSEB field extraction/matching
- batch PDF ordering
- PDF page deletion/reordering
- storage/recovery validation
- Supabase integration where applicable

The beta pipeline is a permanent part of the project's development process, not a one-time test.
