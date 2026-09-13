import { promises as fs } from "node:fs";
import * as path from "node:path";
import type { CheckpointStore, StepOutcome } from "../agent/task-runner";

interface StoredCheckpoint {
  nextIndex: number;
  outcomes: StepOutcome[];
}

export class JsonCheckpointStore implements CheckpointStore {
  private readonly root: string;

  constructor(root: string) {
    this.root = path.resolve(root);
  }

  private file(taskId: string): string {
    const safe = taskId.replace(/[^a-zA-Z0-9_-]/g, "_");
    return path.join(this.root, `${safe}.json`);
  }

  async save(taskId: string, nextIndex: number, outcomes: StepOutcome[]): Promise<void> {
    await fs.mkdir(this.root, { recursive: true });
    const temp = `${this.file(taskId)}.tmp`;
    await fs.writeFile(temp, JSON.stringify({ nextIndex, outcomes }, null, 2), "utf8");
    await fs.rename(temp, this.file(taskId));
  }

  async load(taskId: string): Promise<StoredCheckpoint | undefined> {
    try {
      const raw = await fs.readFile(this.file(taskId), "utf8");
      const value = JSON.parse(raw) as StoredCheckpoint;
      if (!Number.isInteger(value.nextIndex) || !Array.isArray(value.outcomes)) return undefined;
      return value;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
      throw error;
    }
  }
}
