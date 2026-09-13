import test from "node:test";
import assert from "node:assert/strict";
import { DeterministicMcpGateway } from "./mcp-gateway";

test("MCP exposes only declared capabilities", async () => {
  const gateway = new DeterministicMcpGateway();
  const capabilities = await gateway.listCapabilities();
  assert.ok(capabilities.length > 0);
  assert.equal(capabilities.some((item) => item.capability === "desktop.keyboard"), false);
  assert.equal(capabilities.some((item) => item.capability === "browser.navigate"), true);
  await assert.rejects(
    () => gateway.authorize({
      requestId: "bad",
      workspaceId: "test",
      capability: "desktop.keyboard",
      arguments: {},
    }),
    /unsupported/i,
  );
});

test("MCP marks side-effect capabilities for approval", async () => {
  const gateway = new DeterministicMcpGateway();
  const action = await gateway.authorize({
    requestId: "send-1",
    workspaceId: "test",
    capability: "communication.send",
    arguments: { target: "fixture" },
  });
  assert.equal(action.requiresApproval, true);
  assert.equal(action.risk, "sensitive");
});
