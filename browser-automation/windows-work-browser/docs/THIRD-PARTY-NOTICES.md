# Windows Work Browser — Third-Party License Register

This register is a release gate, not a claim that the final distributable is already cleared.

| Component | Exact shipped/runtime version | Intended use | License/status | Release requirement |
|---|---|---|---|---|
| BrowserOS | v0.50.3 | Chromium/Windows browser foundation | AGPL-3.0 | Preserve license/notices and satisfy corresponding-source obligations for distributed modifications. |
| BrowserOS Agent Extension | v0.0.156.0 | Browser agent overlay | Upstream terms | Preserve upstream notices and verify artifact digest. |
| Playwright Core | 1.63.0 | Browser automation/CDP attachment | Apache-2.0 | Preserve license/notice and record in SBOM. |
| @cantoo/pdf-lib | 2.9.2 | PDF merge/split/page export | MIT | Preserve license/notice and record in SBOM. |
| sharp | 0.35.4 | Image crop/resize/deskew/compression | Apache-2.0 | Preserve license/notice and record in SBOM. |
| open-browser-use | Pinned upstream revision required | Browser control integration/reference | MIT | Preserve copyright/license notice when reused. |
| browser-use | Pinned upstream revision required | Agent/browser automation reference | MIT | Preserve copyright/license notice when reused. |
| AutoHotkey | Pinned exact version required before bundling | Windows-native automation | License review required | Do not bundle until exact revision and license are cleared. |
| Noi | Reference only | UI/product reference | License audit required before code reuse | Prefer independent implementation unless reuse is explicitly cleared. |

## Mandatory release evidence

Before `RELEASE CANDIDATE`:

1. Freeze exact dependency revisions/versions.
2. Generate a machine-readable SBOM for the shipped artifact.
3. Generate a human-readable license inventory.
4. Preserve upstream license and attribution files.
5. Record BrowserOS AGPL source/corresponding-source handling for the exact shipped revision.
6. Verify that no reference-only code was copied without license clearance.
7. Attach the SBOM and notices to the release evidence bundle.

The current CI SBOM is dependency inventory evidence. It does not by itself clear upstream licensing or distribution obligations.
