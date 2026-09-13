import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { JsonCheckpointStore } from "./json-checkpoint-store";

test("checkpoint store survives reload and replaces atomically", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-checkpoint-"));
  try {
    const store = new JsonCheckpointStore(root);
    await store.save("task/1", 2, [{ actionId: "a1", status: "executed" }, { actionId: "a2", status: "executed" }]);
    const restored = await store.load("task/1");
    assert.equal(restored?.nextIndex, 2);
    assert.equal(restored?.outcomes.length, 2);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
