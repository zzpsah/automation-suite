import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const root = path.resolve(import.meta.dirname, "..");
const schema = JSON.parse(fs.readFileSync(path.join(root, "schemas", "extraction-result.schema.json"), "utf8"));
const migration = fs.readFileSync(path.join(root, "supabase", "migrations", "0001_document_pipeline.sql"), "utf8");

assert.equal(schema.additionalProperties, false);
assert.ok(schema.properties.priority.enum.includes("URGENT"));
assert.match(migration, /enable row level security/i);
assert.match(migration, /approved_for_publication/i);
assert.match(migration, /security_invoker/i);
assert.doesNotMatch(migration, /service_role\s*=/i);

console.log("Phase 1 validation passed: schema and migration safety markers are present.");
