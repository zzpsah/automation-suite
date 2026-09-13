import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { LocalFileService } from "./local-file-service";
import { DeterministicMcpGateway } from "./mcp-gateway";

test("local file service stays inside workspace", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-files-"));
  try {
    const files = new LocalFileService({ root });
    await files.write("nested/a.txt", new TextEncoder().encode("hello"));
    const entries = await files.list("local", "nested");
    assert.equal(entries.length, 1);
    assert.equal(new TextDecoder().decode(await files.read(entries[0]!)), "hello");
    await assert.rejects(() => files.write("../escape.txt", new Uint8Array([1])));
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("MCP gateway maps only declared capabilities and preserves approval", async () => {
  const gateway = new DeterministicMcpGateway();
  const action = await gateway.authorize({
    requestId: "req-1",
    workspaceId: "ws-1",
    capability: "browser.navigate",
    arguments: { target: "https://example.com", risk: "read" },
  });
  assert.equal(action.capability, "browser.navigate");
  assert.equal(action.requiresApproval, false);

  const outbound = await gateway.authorize({
    requestId: "req-2",
    workspaceId: "ws-1",
    capability: "communication.send",
    arguments: { target: "chat-1", risk: "write" },
  });
  assert.equal(outbound.requiresApproval, true);
});
