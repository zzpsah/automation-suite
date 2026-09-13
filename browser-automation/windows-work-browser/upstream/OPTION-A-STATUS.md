# Option A — Implementation Status

## Current state

`OPTION-A-IMPLEMENTED / NOT-YET-VERIFIED`

## Completed in repository

- Artifact-lane architecture documented.
- Artifact manifest schema added.
- Windows operator runbook added.
- Approved-manifest bootstrap added.
- SHA-256 verification is mandatory before execution.
- Browser launch smoke harness added.
- Verification evidence is written to a dedicated staging/evidence directory.

## Not yet proven

The repository integration environment cannot execute a Windows GUI binary. Therefore these remain pending real Windows evidence:

- successful download of a selected production browser artifact
- trusted release digest verification against the selected artifact
- Windows installation
- real browser launch
- HTTPS rendering
- tabs/windows/profile persistence
- downloads
- Playwright/CDP integration
- native Windows automation bridge
- complete product overlay integration
- signed installer/update/rollback

## Promotion rule

Do not change this status to `OPTION-A-VERIFIED` until the evidence directory contains successful Windows runtime results for the required gates. Do not change overall product status to `PRODUCT-READY` from documentation or CI alone.

## Reproducibility

The selected artifact identity and digest must be frozen in a release manifest. If upstream replaces an asset or changes its digest, create a new candidate instead of mutating an existing verified record.
