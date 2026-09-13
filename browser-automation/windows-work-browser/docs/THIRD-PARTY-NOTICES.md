# Windows Work Browser — Third-Party License Register

This register is a release gate, not a claim that the final distributable is already cleared.

| Component | Intended use | License/status | Release requirement |
|---|---|---|---|
| BrowserOS | Chromium/Windows browser foundation | AGPL-3.0 | Preserve license/notices and satisfy corresponding-source obligations for distributed modifications. |
| open-browser-use | Browser control integration/reference | MIT | Preserve copyright/license notice. |
| browser-use | Agent/browser automation reference | MIT | Preserve copyright/license notice if code is reused. |
| Playwright | Browser automation | License review required | Record exact version and license in generated SBOM. |
| AutoHotkey | Windows-native automation adapter | License review required | Record exact version/license before shipping bundled binaries/scripts. |
| Noi | UI/product reference only | License audit required before code reuse | Prefer independent implementation unless reuse is explicitly cleared. |

## Mandatory release evidence

Before `RELEASE CANDIDATE`:

1. Freeze exact dependency revisions/versions.
2. Generate a machine-readable SBOM for the shipped artifact.
3. Generate a human-readable license inventory.
4. Preserve upstream license and attribution files.
5. Record BrowserOS AGPL source/corresponding-source handling for the exact shipped revision.
6. Verify that no reference-only code was copied without license clearance.
7. Attach the SBOM and notices to the release evidence bundle.

A green contract CI result does not satisfy this legal gate by itself.
