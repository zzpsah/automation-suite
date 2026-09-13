export type TaskStatus =
  | "pending"
  | "running"
  | "paused"
  | "waiting-approval"
  | "recovering"
  | "succeeded"
  | "failed"
  | "cancelled";

export interface TaskCheckpoint {
  taskId: string;
  sequence: number;
  status: TaskStatus;
  nextActionId?: string;
  completedActionIds: string[];
  updatedAt: string;
  evidenceRefs: string[];
}

const TERMINAL: ReadonlySet<TaskStatus> = new Set(["succeeded", "failed", "cancelled"]);

export function canTransition(from: TaskStatus, to: TaskStatus): boolean {
  if (TERMINAL.has(from)) return false;
  if (to === "running") return from === "pending" || from === "paused" || from === "recovering";
  if (to === "waiting-approval") return from === "running" || from === "recovering";
  if (to === "paused") return from === "running" || from === "waiting-approval" || from === "recovering";
  if (to === "recovering") return from === "running";
  return to === "succeeded" || to === "failed" || to === "cancelled";
}

export function assertTransition(from: TaskStatus, to: TaskStatus): void {
  if (!canTransition(from, to)) throw new Error(`Invalid task transition: ${from} -> ${to}`);
}
