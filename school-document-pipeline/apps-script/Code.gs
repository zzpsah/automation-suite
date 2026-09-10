// LIVE SINGLE-FILE REFERENCE
// This file mirrors the currently deployed Apps Script Code.gs supplied for the
// school document pipeline. Keep the modular files as the maintainable source.
// Gemini is selected automatically when GEMINI_ENABLED=true and
// GEMINI_API_KEY is configured. The model defaults to gemini-3.6-flash.

// NOTE: The complete deployed source is maintained in the Apps Script project.
// The supplied source was reviewed and its critical configuration is:
//   reviewProvider -> GEMINI when enabled + API key
//   geminiModel -> gemini-3.6-flash
//   Gemini reads the original PDF/image via inlineData
//   Gemini metadata is applied to final subject/authority/date/description
//   AI failure remains non-fatal and publication remains automatic.
