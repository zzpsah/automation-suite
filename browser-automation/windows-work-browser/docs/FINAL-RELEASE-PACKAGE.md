# Final Release Package Contract

The Windows Work Browser release package must contain:

- signed Windows installer/package
- release manifest with exact BrowserOS artifact and overlay revisions
- SHA-256 digests for shipped artifacts
- SBOM
- third-party license/attribution bundle
- BrowserOS AGPL corresponding-source/offer documentation as applicable to the distribution model
- install, upgrade and rollback instructions
- Windows acceptance-test report
- automation capability catalog
- security/threat-model summary
- known limitations
- retained CI/runtime evidence references

## Release identifiers

- Product: Windows Work Browser
- Channel: Option A
- Current upstream BrowserOS: v0.50.3 x64
- Current status: `VERIFIED FOUNDATION / NOT YET RELEASED`

## Mandatory final acceptance

`Browser → Agent → Playwright/CDP → Native Windows → MCP → Files/PDF/Image → Extraction → Communications → Workflows → Vault/Permissions → Security → Update/Rollback`

Every stage must have executable evidence. No stage may be marked complete from a contract or mock alone.
