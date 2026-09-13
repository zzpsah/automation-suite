import test from "node:test";
import assert from "node:assert/strict";
import { evaluateAction } from "../agent/policy-engine";
import type { AutomationAction, Capability } from "../agent/action-contract";

const base: AutomationAction = {
  id: "policy-test",
  capability: "browser.read",
  risk: "read",
  args: {},
  requiresApproval: false,
  reason: "policy regression test",
};

function withCapability(capability: Capability, risk = base.risk): AutomationAction {
  return { ...base, capability, risk };
}

test("communication.send always requires approval", () => {
  const action = withCapability("communication.send", "write");
  assert.equal(evaluateAction(action).allowed, true);
  assert.equal(evaluateAction(action).requiresApproval, true);
});

test("browser.upload and desktop.print always require approval", () => {
  const upload = withCapability("browser.upload");
  const print = withCapability("desktop.print");
  assert.equal(evaluateAction(upload).requiresApproval, true);
  assert.equal(evaluateAction(print).requiresApproval, true);
});
