import { AutomationAction } from './action-contract';
import { evaluateAction } from './policy-engine';
import { ExecutionContext, Executor, selectExecutor } from './executor-contract';
import { Postcondition, Verifier, assertVerified } from './verification-contract';

export interface PlannedStep {
  action: AutomationAction;
  postcondition?: Postcondition;
}

export interface StepOutcome {
  actionId: string;
  status: 'executed' | 'approval_required' | 'failed';
  result?: unknown;
}

/** Deterministic orchestration skeleton: policy -> approval -> executor -> verification. */
export async function runPlannedSteps(
  steps: PlannedStep[],
  executors: Executor[],
  verifier: Verifier,
  context: Omit<ExecutionContext, 'action'> & { approvalGranted?: (action: AutomationAction) => Promise<boolean> },
): Promise<StepOutcome[]> {
  const outcomes: StepOutcome[] = [];

  for (const step of steps) {
    const decision = evaluateAction(step.action);
    if (!decision.allowed) {
      outcomes.push({ actionId: step.action.id, status: 'failed', result: decision.reason });
      break;
    }

    if (decision.requiresApproval) {
      const granted = context.approvalGranted ? await context.approvalGranted(step.action) : false;
      if (!granted) {
        outcomes.push({ actionId: step.action.id, status: 'approval_required' });
        break;
      }
    }

    try {
      const executor = selectExecutor(executors, step.action);
      const result = await executor.execute(step.action, context);
      if (!result.ok) throw new Error(result.error?.message ?? 'Executor failed.');
      if (step.postcondition) {
        assertVerified(await verifier.verify(step.postcondition));
      }
      outcomes.push({ actionId: step.action.id, status: 'executed', result });
    } catch (error) {
      outcomes.push({ actionId: step.action.id, status: 'failed', result: error instanceof Error ? error.message : String(error) });
      break;
    }
  }

  return outcomes;
}
