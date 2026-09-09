# Security

- Never commit Telegram tokens, Supabase secrets, Google credentials, private Drive IDs, or real school documents.
- Use Apps Script Properties for server-side secrets.
- Public JavaScript may use only a Supabase publishable key protected by RLS.
- Never expose the Supabase service-role key in GitHub Pages or browser code.
- Enable RLS on every table in an exposed schema.
- Public access is restricted to approved records through a public-safe view.
- Student identity, registration, DOB, bank, phone, attendance, and staff-personal records remain private.
- Do not send sensitive documents to an optional AI provider by default.
- Ingestion must be idempotent and restricted to configured Telegram identities and Drive folders.
- Deletion begins as a review request; it never immediately deletes a file or database row.
- Use synthetic fixtures in tests.
