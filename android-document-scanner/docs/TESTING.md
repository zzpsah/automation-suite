# DEVOS Scan — Testing & Verification

## Testing philosophy

The scanner handles real-world photographed documents, so verification must cover both deterministic image-processing logic and Android runtime behavior. CI compilation is necessary but not sufficient for device readiness.

## CI checks

The GitHub Actions workflow is expected to run:

1. Android SDK setup
2. `assembleDebug`
3. `assembleRelease`
4. unit tests
5. APK artifact upload

A successful workflow is required before declaring the Phase 1 build stable.

## Unit-test targets

The first unit-test layer should validate:

- `Quad` rejects anything other than four points.
- corner ordering produces TL/TR/BR/BL for valid quadrilaterals.
- filter selection is deterministic at the API boundary.
- OCR interface can be supplied by a fake provider in tests.
- PDF export handles zero and multiple pages without corrupting session state.

OpenCV image-processing tests should use small fixture images where practical and should verify:

- a clear rectangular document is detected;
- perspective warp returns non-zero dimensions;
- each enhancement mode returns a valid bitmap;
- detector safely returns `null` when no suitable quadrilateral exists.

## Device smoke test checklist

On a physical Android device:

- [ ] First launch shows camera permission request.
- [ ] Denying permission leaves the app in a useful permission state.
- [ ] Granting permission opens the camera.
- [ ] Back camera preview renders correctly.
- [ ] Capture produces a page without crashing.
- [ ] A perspective document is normalized correctly.
- [ ] A no-detection capture falls back safely to the full frame.
- [ ] Multiple pages can be added.
- [ ] Thumbnail selection changes the review page.
- [ ] Manual corner handles respond to dragging.
- [ ] Each filter can be selected and applied.
- [ ] PDF export creates a readable multi-page PDF.
- [ ] App survives rotation/configuration behavior as supported by the current state model.
- [ ] Large photographed forms do not cause an obvious out-of-memory failure.

## Real-form acceptance set

Use representative paperwork rather than only clean blank pages:

1. printed A4 form;
2. skewed photographed form;
3. form with uneven lighting/shadows;
4. handwritten entries;
5. checkboxes;
6. photo embedded in the form;
7. signature area;
8. low-contrast printed text;
9. border/background similar to the paper;
10. multi-page form batch.

The acceptance set is especially important before connecting the scanner to government/school OCR or database workflows.

## Verification terminology

- **Implemented**: code exists and is wired into the application.
- **CI verified**: GitHub Actions completed the relevant build/test step successfully.
- **Device verified**: exercised on an actual Android device/emulator.
- **Production ready**: all required release gates passed and known limitations are acceptable.

Do not substitute one level for another.
