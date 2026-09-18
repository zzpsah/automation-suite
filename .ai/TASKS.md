# Tasks

## Active
- Keep repository-level DevOS context synchronized.
- Preserve module boundaries and provenance.
- Validate `browser-portal-automation/udise/student-profile/` against one authenticated UDISE+ test student in read-only mode.
- Capture exact General Profile, Education Profile and Facility Profile structures.
- Populate schema files only from observed fields/selectors.
- Verify checkpoint/recovery and read-only evidence capture.

## Planned
- Add schema-driven extraction after field discovery.
- Add approved-source adapters for Supabase/master data without copying private datasets into Git.
- Add Class XI Education Profile source selection using OFSS → e-Shiksha Kosh → UDISE status → Siwan Dropbox fallback.
- Add review UI/report for per-field comparison and proposed values.
- Add explicit per-field approval model.
- Implement APPLY only after selector/schema stability is proven.
- Implement SUBMIT as a separate explicit authorization gate.
- Add unit/integration tests around discovered schema and safe write gates.
- Add module-specific semantic session notes after each significant portal discovery.

## Blocked
- Stable GP/EP/FP selectors and exact field lists are intentionally blocked until an authenticated real-page discovery run is completed.
- Write-enabled APPLY/SUBMIT remains intentionally blocked until the read-only workflow is verified and explicit approval semantics are implemented.
