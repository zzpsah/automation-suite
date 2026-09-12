# DEVOS Scan — Changelog

## Unreleased / Phase 1

### Added
- Kotlin + Jetpack Compose Android scanner foundation.
- CameraX high-quality back-camera capture.
- OpenCV post-capture document quadrilateral detection.
- Four-point perspective normalization.
- Manual four-corner editor.
- Original, Auto/CLAHE, Mono and adaptive B&W filters.
- In-memory multi-page batch review.
- Android `PdfDocument` PDF export.
- Provider-independent `OcrEngine` interface.
- GitHub Actions build/test/APK artifact workflow.
- Premium dark-mode scanner UI.
- Architecture, status and testing documentation.

### Fixed
- Added the missing Compose `Image` import in `MainActivity.kt`, commit `c77d7765b032e66362eacf3a85c128e17b8ccaba`.

### Verification
- Initial CI run `34713455738` failed during Kotlin compilation.
- Follow-up CI run `34713732903` was started from the import-fix commit and was building the APK when the documentation pass was recorded.

### Known limitations
- Automatic document detection currently occurs after capture rather than continuously over the live preview.
- Manual corner editing currently operates on the already-warped page; true source-image re-warping is a Phase 2 correction.
- Flash UI state is not yet wired to `ImageCapture` flash mode.
- PDF currently exports to application cache rather than a user-selected SAF destination.
- Batch state is not persisted across process death.
- OCR provider is not bundled yet.
- Device/emulator smoke testing remains outstanding until an Android runtime is available.
