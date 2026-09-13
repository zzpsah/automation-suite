export interface WorkflowTrigger {
  kind: "manual" | "schedule" | "file-created" | "message-received" | "browser-event";
  value?: string;
}

export interface WorkflowStepRef {
  id: string;
  actionId: string;
  continueOnFailure?: boolean;
  retryLimit?: number;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  triggers: WorkflowTrigger[];
  steps: WorkflowStepRef[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowRun {
  id: string;
  workflowId: string;
  state: "queued" | "running" | "waiting" | "paused" | "completed" | "failed" | "cancelled";
  currentStep: number;
  checkpoint?: string;
  startedAt: string;
  updatedAt: string;
}

export interface WorkflowEngine {
  validate(definition: WorkflowDefinition): Promise<void>;
  start(workflowId: string, input?: Record<string, unknown>): Promise<WorkflowRun>;
  pause(runId: string): Promise<void>;
  resume(runId: string): Promise<WorkflowRun>;
  cancel(runId: string): Promise<void>;
}

export function assertWorkflow(definition: WorkflowDefinition): void {
  if (!definition.id || !definition.name) throw new Error("Workflow id and name are required.");
  if (definition.steps.length === 0) throw new Error("Workflow must contain at least one step.");
  if (definition.steps.some((s) => (s.retryLimit ?? 0) < 0 || (s.retryLimit ?? 0) > 5)) {
    throw new Error("Retry limit must be between 0 and 5.");
  }
}
