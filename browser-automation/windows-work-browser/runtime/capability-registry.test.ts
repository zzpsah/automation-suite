import test from "node:test";
import assert from "node:assert/strict";
import { CAPABILITIES, findCapability } from "./capability-registry.js";

test("registry contains core browser and desktop capabilities", () => {
  assert.ok(CAPABILITIES.some((c) => c.capability === "browser.navigate"));
  assert.ok(CAPABILITIES.some((c) => c.capability === "desktop.file_dialog"));
  assert.ok(CAPABILITIES.some((c) => c.capability === "pdf.process"));
  assert.ok(CAPABILITIES.some((c) => c.capability === "communication.send"));
});

test("dangerous capabilities are explicitly classified", () => {
  assert.equal(findCapability("files.delete").defaultRisk, "destructive");
  assert.equal(findCapability("communication.send").defaultRisk, "sensitive");
  assert.equal(findCapability("browser.upload").defaultRisk, "sensitive");
});

test("unknown capabilities are rejected", () => {
  assert.throws(() => findCapability("not-a-real-capability" as never));
});
