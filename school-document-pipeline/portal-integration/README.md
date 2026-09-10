# Public portal integration

## Private document manager (deployed)

Staging URL: https://zzpsah.github.io/umv-tetahali-staging/private-documents.html

The authenticated manager uses `assets/private-document-manager.js` and the
publishable configuration in `assets/document-archive-config.js`. It reads the
private `documents` table, displays Drive links and statuses, supports filters,
and subscribes to Supabase Realtime. `Run AI Review` calls the protected
`request_document_ai_review` RPC; Apps Script processes the queue every five minutes.

Current access: the existing profile admin and trusted JWT reviewer/admin roles.
The final request implementation is in migration
`20260910132000_review_request_authorization.sql`: missing roles are rejected,
the document row is locked while queuing, and repeated requests reuse active jobs.
Credentials are never placed in the frontend. Source originals remain on Drive.

Verification: the deployed HTML and JavaScript returned HTTP 200. Transactional
database tests confirmed profile-admin read/request access and denied a signed-in
non-admin with absent app metadata. Test writes were rolled back. An actual
signed-in browser session is still needed to verify rendering and the button
end to end. Do not describe that check as completed.

OCR is currently Google Drive OCR plus rules. AI status `Completed` means the
tool finished, not that the document was approved. The test PDF remains
`Needs Manual Review`; reference/date were filename-derived. The current PDF
OCR path converts the entire PDF, so strict first-page-only processing remains
an outstanding implementation requirement.

This module reads only `approved_public_documents`. Configure the Supabase project URL and publishable key in the staging portal. Never include a service-role or secret key.

Before deployment:

1. Apply and verify the migration in a non-production Supabase project.
2. Confirm anonymous reads return approved, non-sensitive records only.
3. Confirm private and unapproved records return no rows.
4. Integrate into the verified staging website repository.
5. Test accessibility, mobile layout, error handling, and low-bandwidth behavior.
