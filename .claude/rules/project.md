# School Document Pipeline Rules

- Treat the existing pipeline as production code.
- Prefer the smallest safe change over broad rewrites.
- Keep GovDOC OCR reusable and isolated behind the adapter.
- Require tests for changes to OCR mapping, storage handling, lifecycle state, duplicate handling, or publication.
- Keep offline tests free of Supabase, B2, Drive, Telegram, and publication side effects.
- Never use fake production credentials or invent storage state to make a test pass.
- Record evidence and failure reasons clearly enough for the next debugging session.
