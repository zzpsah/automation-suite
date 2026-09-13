# Windows Work Browser — Final Release Checklist

## Preconditions

- [ ] `BUILD-STATUS.md` says `RELEASE CANDIDATE READY`.
- [ ] Windows artifact pin and digest are frozen.
- [ ] Agent/runtime CI is green.
- [ ] Contract/security CI is green.
- [ ] Windows browser E2E is green on the exact release commit.
- [ ] MCP, native Windows, extraction, files, PDF/image, communications, workflow and vault runtime E2E are green.
- [ ] SBOM generated from the release dependency lockfile.
- [ ] Third-party notices and BrowserOS AGPL corresponding-source material are attached.
- [ ] Installer/update signing credentials are available to the protected release workflow.

## Release command

Create an immutable tag matching `wwb-vMAJOR.MINOR.PATCH` on the exact candidate commit. The release workflow builds the agent package, stages the pinned BrowserOS artifact, verifies SHA-256 and Authenticode, assembles the release bundle, and publishes the GitHub Release with the evidence package.

## Release artifacts

- Windows Work Browser installer/package
- BrowserOS provenance manifest
- Agent runtime bundle
- SBOM (CycloneDX JSON)
- Third-party notices
- Install/upgrade/rollback runbook
- Capability catalog
- Security summary
- Windows acceptance report
- SHA-256 digest manifest

## Fail-closed rule

The release workflow must stop before publishing if any mandatory runtime gate, digest, signature, SBOM, license package, or signing credential is missing. A successful build of the agent package alone cannot publish a product release.

## Post-release

- [ ] Verify GitHub release asset hashes.
- [ ] Verify installation on a clean Windows machine.
- [ ] Verify update and rollback from the previous verified release.
- [ ] Record final evidence URLs and release commit in `BUILD-STATUS.md`.
