import test from "node:test";
import assert from "node:assert/strict";
import { evaluateAction } from "../agent/policy-engine";
import type { AutomationAction } from "../agent/action-contract";

const base: AutomationAction = {
  id: "policy-test",
  capability: "browser.read",
  risk: "read",
  args: {},
  requiresApproval: false,
  reason: "policy regression test",
};

test("communication.send always requires approval", () => {
  const action = { ...base, capability: "communication.send", risk: "write" as const };
  assert.equal(evaluateAction(action).allowed, true);
  assert.equal(evaluateAction(action).requiresApproval, true);
});

test("browser.upload and desktop.print always require approval", () => {
  const upload = { ...base, capability: "browser.upload" };
  const print = { ...base, capability: "desktop.print" };
  assert.equal(evaluateAction(upload).requiresApproval, true);
  assert.equal(evaluateAction(print).requiresApproval, true);
});
