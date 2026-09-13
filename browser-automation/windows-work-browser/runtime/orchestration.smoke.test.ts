import test from "node:test";
import assert from "node:assert/strict";
import { runPlannedSteps, type CheckpointStore } from "../agent/task-runner.js";
import type { AutomationAction, ActionResult } from "../agent/action-contract.js";
import type { Executor, ExecutionContext } from "../agent/executor-contract.js";
import type { Postcondition, Verifier, VerificationResult } from "../agent/verification-contract.js";

const action: AutomationAction = {
  id: "smoke.navigate",
  capability: "browser.navigate",
  risk: "read",
  target: "https://example.com",
  args: {},
  requiresApproval: false,
  reason: "Navigate to smoke-test page.",
};

class FakeExecutor implements Executor {
  readonly kind = "playwright" as const;
  supports(candidate: AutomationAction): boolean { return candidate.capability === "browser.navigate"; }
  async execute(candidate: AutomationAction, _context: ExecutionContext): Promise<ActionResult> {
    return { actionId: candidate.id, ok: true, output: candidate.target };
  }
}

class FakeVerifier implements Verifier {
  async verify(postcondition: Postcondition): Promise<VerificationResult> {
    return { postconditionId: postcondition.id, passed: true, observed: postcondition.expected, summary: "Expected state observed." };
  }
}

class MemoryCheckpoint implements CheckpointStore {
  private value?: { nextIndex: number; outcomes: Array<{ actionId: string; status: "executed" | "approval_required" | "failed" | "skipped"; result?: unknown }> };
  async save(_taskId: string, nextIndex: number, outcomes: Array<{ actionId: string; status: "executed" | "approval_required" | "failed" | "skipped"; result?: unknown }>): Promise<void> {
    this.value = { nextIndex, outcomes: [...outcomes] };
  }
  async load(_taskId: string): Promise<typeof this.value> { return this.value; }
}

test("policy -> executor -> verifier -> checkpoint succeeds", async () => {
  const checkpoints = new MemoryCheckpoint();
  const postcondition: Postcondition = {
    id: "smoke.url",
    method: "url",
    description: "Page reached expected URL",
    expected: { url: "https://example.com" },
  };

  const outcomes = await runPlannedSteps(
    "smoke-task",
    [{ action, postcondition }],
    [new FakeExecutor()],
    new FakeVerifier(),
    { workspaceId: "test" },
    undefined,
    checkpoints,
  );

  assert.equal(outcomes.length, 1);
  assert.equal(outcomes[0]?.status, "executed");
  assert.equal((await checkpoints.load("smoke-task"))?.nextIndex, 1);
});

test("sensitive action stops without approval callback", async () => {
  const sensitive: AutomationAction = {
    ...action,
    id: "smoke.upload",
    capability: "browser.upload",
    risk: "sensitive",
    target: "input[type=file]",
    args: { filePath: "safe-file-token" },
    reason: "Upload a prepared test file.",
  };

  const outcomes = await runPlannedSteps(
    "approval-task",
    [{ action: sensitive }],
    [new FakeExecutor()],
    new FakeVerifier(),
    { workspaceId: "test" },
  );

  assert.equal(outcomes[0]?.status, "approval_required");
});
