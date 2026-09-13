# Option A — Windows Operator Runbook

## Prerequisites

- Windows x64 machine
- Git and PowerShell
- Internet access to the approved upstream release source
- Sufficient disk space for the selected artifact and staging area
- Permission to install/run the browser

## Procedure

1. Select an approved upstream Windows artifact.
2. Record release/tag or immutable revision and SHA-256 in the artifact manifest.
3. Download into a staging directory, not directly into the production install directory.
4. Compute SHA-256 and compare with the trusted release digest.
5. Reject the artifact on any mismatch or missing trusted digest.
6. Install/launch the browser and run the browser smoke suite.
7. Deploy the Work Browser overlay using a supported integration method.
8. Verify the automation bridge exposes only declared capabilities.
9. Run read-only automation first, then approved write actions.
10. Capture evidence and retain the exact artifact and overlay identifiers.
11. Promote only when all required gates pass.

## Rollback

Keep the previous verified artifact until the new candidate passes smoke tests. On failure, disable the candidate, restore the previous verified artifact, preserve failure evidence, and do not silently retry sensitive/destructive actions.

## Promotion states

`DISCOVERED -> STAGED -> VERIFIED -> INSTALLED -> SMOKE-PASSED -> OVERLAY-PASSED -> CANDIDATE`

Failure states are terminal for that candidate until a new artifact or corrected overlay is supplied.

## Security rules

- Never log passwords, tokens, OTPs, cookies, or credential values.
- Never give the model arbitrary PowerShell, AHK, or shell execution.
- All automation actions pass through the common action contract and policy gate.
- Human approval remains required for sensitive/destructive operations and final external submissions.
