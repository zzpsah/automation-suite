import test from "node:test";
import assert from "node:assert/strict";
import { DeterministicMcpGateway } from "./mcp-gateway";
import { handleRpc } from "./mcp-stdio-server";

let output = "";
const originalWrite = process.stdout.write.bind(process.stdout);

test.beforeEach(() => {
  output = "";
  process.stdout.write = ((chunk: string | Uint8Array) => {
    output += typeof chunk === "string" ? chunk : Buffer.from(chunk).toString();
    return true;
  }) as typeof process.stdout.write;
});

test.afterEach(() => {
  process.stdout.write = originalWrite;
});

test("stdio initialize and tool listing", async () => {
  const gateway = new DeterministicMcpGateway();
  await handleRpc(gateway, { jsonrpc: "2.0", id: 1, method: "initialize" });
  const initialized = JSON.parse(output);
  assert.equal(initialized.result.serverInfo.name, "windows-work-browser");

  output = "";
  await handleRpc(gateway, { jsonrpc: "2.0", id: 2, method: "tools/list" });
  const listed = JSON.parse(output);
  assert.ok(listed.result.tools.some((tool: { name: string }) => tool.name === "browser.navigate"));
});

test("stdio tools/call creates an approval-bound automation action", async () => {
  const gateway = new DeterministicMcpGateway();
  await handleRpc(gateway, {
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: {
      name: "communication.send",
      arguments: { workspaceId: "test", destination: "fixture", body: "hello" },
    },
  });
  const response = JSON.parse(output);
  assert.equal(response.result.isError, false);
  const value = JSON.parse(response.result.content[0].text);
  assert.equal(value.authorized, true);
  assert.equal(value.action.capability, "communication.send");
  assert.equal(value.action.requiresApproval, true);
});
