export type TaskState =
  | "queued"
  | "observing"
  | "planning"
  | "awaiting_approval"
  | "executing"
  | "verifying"
  | "recovering"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export interface TaskCheckpoint {
  taskId: string;
  state: TaskState;
  actionIndex: number;
  completedActionIds: string[];
  evidenceRefs: string[];
  resumable: boolean;
  updatedAt: string;
}

export interface AutomationTask {
  id: string;
  goal: string;
  state: TaskState;
  actions: string[];
  checkpoint: TaskCheckpoint;
  createdAt: string;
  updatedAt: string;
}

export function canResume(checkpoint: TaskCheckpoint): boolean {
  return checkpoint.resumable && !["completed", "cancelled"].includes(checkpoint.state);
}
