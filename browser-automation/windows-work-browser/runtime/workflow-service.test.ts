import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { DeterministicWorkflowService } from "./workflow-service";

test("workflow service checkpoints completed steps and supports pause/resume", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-workflow-"));
  try {
    const service = new DeterministicWorkflowService(root);
    const events: string[] = [];
    const created = await service.create("demo", {
      steps: [
        { id: "a", run: async () => { events.push("a"); } },
        { id: "b", run: async () => { events.push("b"); } },
      ],
    });
    const task = await service.run(created.id);
    for (let i = 0; i < 20 && events.length < 2; i += 1) await new Promise((resolve) => setTimeout(resolve, 10));
    assert.deepEqual(events, ["a", "b"]);
    await service.pause(task.taskId);
    await service.resume(task.taskId);
    assert.equal(events.filter((value) => value === "a").length, 1);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
