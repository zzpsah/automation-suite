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
  status: 'executed' | 'approval_required' | 'failed' | 'skipped';
  result?: unknown;
}

export interface CheckpointStore {
  save(taskId: string, nextIndex: number, outcomes: StepOutcome[]): Promise<void>;
  load(taskId: string): Promise<{ nextIndex: number; outcomes: StepOutcome[] } | undefined>;
}

/** Deterministic orchestration: policy -> approval -> executor -> verification -> checkpoint. */
export async function runPlannedSteps(
  taskId: string,
  steps: PlannedStep[],
  executors: Executor[],
  verifier: Verifier,
  context: Omit<ExecutionContext, 'taskId'>,
  approvalGranted?: (action: AutomationAction) => Promise<boolean>,
  checkpointStore?: CheckpointStore,
): Promise<StepOutcome[]> {
  const stored = checkpointStore ? await checkpointStore.load(taskId) : undefined;
  const outcomes: StepOutcome[] = stored?.outcomes ? [...stored.outcomes] : [];
  const startIndex = stored?.nextIndex ?? 0;

  for (let index = startIndex; index < steps.length; index += 1) {
    const step = steps[index];
    const decision = evaluateAction(step.action);
    if (!decision.allowed) {
      outcomes.push({ actionId: step.action.id, status: 'failed', result: decision.reason });
      await checkpointStore?.save(taskId, index, outcomes);
      break;
    }

    if (decision.requiresApproval) {
      const granted = approvalGranted ? await approvalGranted(step.action) : false;
      if (!granted) {
        outcomes.push({ actionId: step.action.id, status: 'approval_required' });
        await checkpointStore?.save(taskId, index, outcomes);
        break;
      }
    }

    try {
      const executor = selectExecutor(executors, step.action);
      const result = await executor.execute(step.action, { ...context, taskId });
      if (!result.ok) throw new Error(result.error?.message ?? 'Executor failed.');
      if (step.postcondition) assertVerified(await verifier.verify(step.postcondition));
      outcomes.push({ actionId: step.action.id, status: 'executed', result });
      await checkpointStore?.save(taskId, index + 1, outcomes);
    } catch (error) {
      outcomes.push({ actionId: step.action.id, status: 'failed', result: error instanceof Error ? error.message : String(error) });
      await checkpointStore?.save(taskId, index, outcomes);
      break;
    }
  }

  return outcomes;
}
