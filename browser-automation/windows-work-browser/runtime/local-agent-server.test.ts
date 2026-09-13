import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { createLocalAgentServer } from "./local-agent-server";

test("local agent bridge accepts and lists a browser task", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-agent-"));
  const { server } = createLocalAgentServer({ queueFile: path.join(root, "tasks.json"), workspaceId: "test-workspace" });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const address = server.address();
  assert.ok(address && typeof address === "object");
  const base = `http://127.0.0.1:${address.port}`;
  try {
    const health = await fetch(`${base}/health`);
    assert.equal(health.status, 200);
    assert.equal((await health.json()).ok, true);

    const create = await fetch(`${base}/tasks`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ goal: "Extract fixture records", tabId: 7 }),
    });
    assert.equal(create.status, 202);
    const accepted = await create.json();
    assert.equal(accepted.accepted, true);
    assert.equal(accepted.task.workspaceId, "test-workspace");
    assert.equal(accepted.task.source, "extension");

    const list = await fetch(`${base}/tasks`);
    const listed = await list.json();
    assert.equal(listed.tasks.length, 1);
    assert.equal(listed.tasks[0].goal, "Extract fixture records");

    const bad = await fetch(`${base}/tasks`, { method: "POST", body: "[]" });
    assert.equal(bad.status, 400);
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
    await rm(root, { recursive: true, force: true });
  }
});
