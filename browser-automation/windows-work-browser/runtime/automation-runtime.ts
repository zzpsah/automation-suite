import type { AutomationAction, ActionResult } from "../agent/action-contract";
import { evaluateAction } from "../agent/policy-engine";
import { selectExecutor, type ExecutionContext, type Executor } from "../agent/executor-contract";
import { assertVerified, type Postcondition, type Verifier } from "../agent/verification-contract";
import { assertSafeEvidence, type EvidenceRecord } from "../agent/evidence-schema";

export interface RuntimeApproval {
  approve(action: AutomationAction): Promise<boolean>;
}

export interface RuntimeEvidenceSink {
  append(record: EvidenceRecord): Promise<void>;
}

export interface RuntimeStep {
  action: AutomationAction;
  postcondition?: Postcondition;
}

export interface RuntimeStepResult {
  actionId: string;
  ok: boolean;
  status: "executed" | "approval_required" | "denied" | "failed";
  result?: ActionResult;
  error?: string;
}

/**
 * Central runtime coordinator. This is intentionally AI-provider agnostic:
 * callers provide structured actions, while policy/approval/execution/
 * verification/evidence remain deterministic and shared by all agents.
 */
export class AutomationRuntime {
  constructor(
    private readonly executors: Executor[],
    private readonly verifier: Verifier,
    private readonly approval: RuntimeApproval,
    private readonly evidence: RuntimeEvidenceSink,
  ) {}

  async runStep(taskId: string, workspaceId: string, step: RuntimeStep): Promise<RuntimeStepResult> {
    const started = new Date().toISOString();
    const decision = evaluateAction(step.action);
    if (!decision.allowed) {
      return { actionId: step.action.id, ok: false, status: "denied", error: decision.reason };
    }

    if (decision.requiresApproval && !(await this.approval.approve(step.action))) {
      return { actionId: step.action.id, ok: false, status: "approval_required" };
    }

    try {
      const executor = selectExecutor(this.executors, step.action);
      const result = await executor.execute(step.action, { taskId, workspaceId } as ExecutionContext);
      if (!result.ok) throw new Error(result.error?.message ?? "Executor failed");
      if (step.postcondition) assertVerified(await this.verifier.verify(step.postcondition));

      const record: EvidenceRecord = {
        actionId: step.action.id,
        timestamp: started,
        capability: step.action.capability,
        risk: step.action.risk,
        policy: decision.requiresApproval ? "approval_required" : "allowed",
        executor: executor.kind,
        outcome: "success",
        verification: step.postcondition
          ? { method: step.postcondition.method, passed: true, summary: step.postcondition.description }
          : undefined,
      };
      assertSafeEvidence(record);
      await this.evidence.append(record);
      return { actionId: step.action.id, ok: true, status: "executed", result };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const record: EvidenceRecord = {
        actionId: step.action.id,
        timestamp: started,
        capability: step.action.capability,
        risk: step.action.risk,
        policy: "allowed",
        executor: "service",
        outcome: "failure",
        error: { code: "RUNTIME_FAILURE", recoverable: true },
      };
      assertSafeEvidence(record);
      await this.evidence.append(record);
      return { actionId: step.action.id, ok: false, status: "failed", error: message };
    }
  }
}
