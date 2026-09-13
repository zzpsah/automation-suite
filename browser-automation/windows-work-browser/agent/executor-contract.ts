import { ActionResult, AutomationAction } from "./action-contract";

export type ExecutorKind = "playwright" | "cdp" | "windows-native" | "service";

export interface ExecutionContext {
  taskId: string;
  workspaceId: string;
  signal?: AbortSignal;
}

export interface Executor {
  readonly kind: ExecutorKind;
  supports(action: AutomationAction): boolean;
  execute(action: AutomationAction, context: ExecutionContext): Promise<ActionResult>;
}

/**
 * Executors are adapters only. The orchestrator/policy engine decides whether
 * an action may run; an executor must never broaden the requested capability.
 */
export function selectExecutor(executors: Executor[], action: AutomationAction): Executor {
  const executor = executors.find((candidate) => candidate.supports(action));
  if (!executor) throw new Error(`No executor registered for capability: ${action.capability}`);
  return executor;
}
