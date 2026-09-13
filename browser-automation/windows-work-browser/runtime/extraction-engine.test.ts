import test from "node:test";
import assert from "node:assert/strict";
import { deduplicateRecords, runExtraction } from "./extraction-engine";

test("extraction removes duplicate records by stable key", () => {
  const result = deduplicateRecords([
    { id: "1", name: "A" },
    { id: "1", name: "A duplicate" },
    { id: "2", name: "B" },
  ], ["id"]);
  assert.equal(result.records.length, 2);
  assert.equal(result.removed, 1);
});

test("extraction verifies count and required fields", () => {
  const result = runExtraction({
    expectedCount: 2,
    deduplicateBy: ["id"],
    records: [
      { id: "1", name: "A" },
      { id: "1", name: "A" },
      { id: "2", name: "B" },
    ],
  }, ["id", "name"], "csv");
  assert.equal(result.duplicatesRemoved, 1);
  assert.equal(result.missingFieldCount, 0);
  assert.equal(result.countVerified, true);
  assert.match(result.exported, /"id","name"/);
});
