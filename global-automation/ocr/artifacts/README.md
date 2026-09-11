# Controlled OCR artifacts

Large models and runtime binaries are **not committed to Git**. Production installs consume only immutable, versioned artifacts recorded in `manifest.json` and verified with SHA-256 before use.

Rules:
- never resolve `latest` in production;
- pin an explicit artifact version;
- record backend and language compatibility;
- record SHA-256 and expected size;
- fail closed on checksum mismatch;
- keep release/rollback metadata with the artifact;
- runtime code must never silently download an unpinned model.
