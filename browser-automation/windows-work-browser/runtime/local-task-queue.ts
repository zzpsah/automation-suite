import { promises as fs } from "node:fs";
import * as path from "node:path";

export interface TaskIntent {
  id: string;
  goal: string;
  tabId?: number;
  workspaceId: string;
  source: "extension" | "mcp" | "api";
  createdAt: string;
}

export class LocalTaskQueue {
  constructor(private readonly file: string) {}

  private async read(): Promise<TaskIntent[]> {
    try {
      return JSON.parse(await fs.readFile(this.file, "utf8")) as TaskIntent[];
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    }
  }

  private async write(items: TaskIntent[]): Promise<void> {
    await fs.mkdir(path.dirname(this.file), { recursive: true });
    const temp = `${this.file}.tmp-${process.pid}-${Date.now()}`;
    await fs.writeFile(temp, JSON.stringify(items, null, 2), "utf8");
    await fs.rename(temp, this.file);
  }

  async enqueue(intent: TaskIntent): Promise<TaskIntent> {
    const goal = intent.goal.trim();
    if (!goal) throw new Error("Task goal is required.");
    if (goal.length > 20_000) throw new Error("Task goal is too large.");
    const items = await this.read();
    if (items.some((item) => item.id === intent.id)) throw new Error(`Task already exists: ${intent.id}`);
    items.push({ ...intent, goal, createdAt: intent.createdAt || new Date().toISOString() });
    await this.write(items);
    return intent;
  }

  async list(limit = 100): Promise<ReadonlyArray<TaskIntent>> {
    return (await this.read()).slice(-Math.max(1, Math.min(1000, limit)));
  }
}
