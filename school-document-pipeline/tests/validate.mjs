import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const root = path.resolve(import.meta.dirname, "..");
const schema = JSON.parse(fs.readFileSync(path.join(root, "schemas", "extraction-result.schema.json"), "utf8"));
const migration = fs.readFileSync(path.join(root, "supabase", "migrations", "0001_document_pipeline.sql"), "utf8");
const config = fs.readFileSync(path.join(root, "apps-script", "Config.gs"), "utf8");
const driveScanner = fs.readFileSync(path.join(root, "apps-script", "DriveScanner.gs"), "utf8");
const telegramWebhook = fs.readFileSync(path.join(root, "apps-script", "TelegramWebhook.gs"), "utf8");
const geminiAssistant = fs.readFileSync(path.join(root, "apps-script", "GeminiAssistant.gs"), "utf8");
const aiReviewQueue = fs.readFileSync(path.join(root, "apps-script", "AiReviewQueue.gs"), "utf8");
const extraction = fs.readFileSync(path.join(root, "apps-script", "Extraction.gs"), "utf8");
const taxonomyMigration = fs.readFileSync(
  path.join(root, "supabase", "migrations", "20260909182635_resilient_document_taxonomy.sql"),
  "utf8"
);

assert.equal(schema.additionalProperties, false);
assert.ok(schema.properties.priority.enum.includes("URGENT"));
assert.match(migration, /enable row level security/i);
assert.match(migration, /approved_for_publication/i);
assert.match(migration, /security_invoker/i);
assert.doesNotMatch(migration, /service_role\s*=/i);
assert.match(config, /Math\.max\(1, Math\.min\(50/);
assert.match(driveScanner, /moveToProcessing_\(file\)/);
assert.match(telegramWebhook, /moveToProcessing_\(file\)/);
assert.match(telegramWebhook, /function registerTelegramWebhook\(\)/);
assert.match(geminiAssistant, /function geminiSuggest_\(file, extraction\)/);
assert.match(geminiAssistant, /responseMimeType/);
assert.match(aiReviewQueue, /function processAiReviewQueue\(\)/);
assert.match(aiReviewQueue, /changes\.ai_suggestion_status = 'Completed'/);
assert.match(extraction, /MANUAL_FIRST_PAGE_REQUIRED/);
assert.match(extraction, /\^image\\\//);
assert.match(extraction, /application\/pdf/);
assert.match(extraction, /function configureFreeReviewMode\(\)/);
assert.match(extraction, /suggestCategory_/);
assert.match(taxonomyMigration, /document_category_definitions/);
assert.match(taxonomyMigration, /preserve_category_definition_history/);
assert.match(taxonomyMigration, /search_vector/);
assert.match(taxonomyMigration, /security_invoker/i);

console.log("Pipeline validation passed: schema, migration safety, and queue movement markers are present.");
