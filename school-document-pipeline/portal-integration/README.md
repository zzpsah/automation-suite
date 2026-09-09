# Public portal integration

This module reads only `approved_public_documents`. Configure the Supabase project URL and publishable key in the staging portal. Never include a service-role or secret key.

Before deployment:

1. Apply and verify the migration in a non-production Supabase project.
2. Confirm anonymous reads return approved, non-sensitive records only.
3. Confirm private and unapproved records return no rows.
4. Integrate into the verified staging website repository.
5. Test accessibility, mobile layout, error handling, and low-bandwidth behavior.
