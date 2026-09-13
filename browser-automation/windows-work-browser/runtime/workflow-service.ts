import type { WorkflowService } from "./capability-services";
import { JsonCheckpointStore } from "./json-checkpoint-store";

export interface WorkflowStep {
  id: string;
  run(input: unknown): Promise<unknown>;
}

export interface WorkflowDefinition {
  steps: WorkflowStep[];
}

export class DeterministicWorkflowService implements WorkflowService {
  private readonly workflows = new Map<string, WorkflowDefinition>();
  private readonly tasks = new Map<string, { workflowId: string; input: unknown; index: number; status: "running" | "paused" | "cancelled" | "completed" | "failed" }>();
  private readonly checkpoints: JsonCheckpointStore;

  constructor(checkpointRoot: string) {
    this.checkpoints = new JsonCheckpointStore(checkpointRoot);
  }

  async create(name: string, definition: unknown): Promise<{ id: string }> {
    const id = `${name.replace(/[^a-zA-Z0-9_-]/g, "_")}-${this.workflows.size + 1}`;
    if (!definition || typeof definition !== "object" || !Array.isArray((definition as WorkflowDefinition).steps)) {
      throw new Error("Workflow definition must contain steps[].");
    }
    this.workflows.set(id, definition as WorkflowDefinition);
    return { id };
  }

  async run(id: string, input?: unknown): Promise<{ taskId: string }> {
    if (!this.workflows.has(id)) throw new Error(`Unknown workflow: ${id}`);
    const taskId = `task-${Date.now()}-${this.tasks.size + 1}`;
    this.tasks.set(taskId, { workflowId: id, input, index: 0, status: "running" });
    void this.execute(taskId);
    return { taskId };
  }

  private async execute(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) return;
    const workflow = this.workflows.get(task.workflowId);
    if (!workflow) { task.status = "failed"; return; }
    try {
      const saved = await this.checkpoints.load(taskId);
      let index = saved?.nextIndex ?? task.index;
      const outcomes = saved?.outcomes ?? [];
      while (index < workflow.steps.length) {
        const current = this.tasks.get(taskId);
        if (!current || current.status === "cancelled") return;
        if (current.status === "paused") return;
        const step = workflow.steps[index];
        if (!step) throw new Error(`Workflow step ${index} is missing.`);
        const result = await step.run(current.input);
        outcomes.push({ actionId: step.id, status: "executed", result });
        index += 1;
        current.index = index;
        await this.checkpoints.save(taskId, index, outcomes);
      }
      task.status = "completed";
    } catch {
      task.status = "failed";
    }
  }

  async pause(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Unknown task: ${taskId}`);
    task.status = "paused";
  }

  async resume(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Unknown task: ${taskId}`);
    if (task.status === "cancelled" || task.status === "completed") throw new Error(`Task ${taskId} cannot be resumed.`);
    task.status = "running";
    void this.execute(taskId);
  }

  async cancel(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Unknown task: ${taskId}`);
    task.status = "cancelled";
  }
}
