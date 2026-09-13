import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { randomUUID } from "node:crypto";
import { LocalTaskQueue, type TaskIntent } from "./local-task-queue";

export interface LocalAgentServerOptions {
  port?: number;
  queueFile: string;
  workspaceId?: string;
}

function json(response: ServerResponse, status: number, body: unknown): void {
  response.statusCode = status;
  response.setHeader("content-type", "application/json; charset=utf-8");
  response.end(JSON.stringify(body));
}

async function body(request: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.from(chunk));
  if (!Buffer.concat(chunks).length) return {};
  const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8")) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("JSON object required.");
  return parsed as Record<string, unknown>;
}

export function createLocalAgentServer(options: LocalAgentServerOptions) {
  const queue = new LocalTaskQueue(options.queueFile);
  const server = createServer(async (request, response) => {
    try {
      if (request.method === "GET" && request.url === "/health") {
        json(response, 200, { ok: true, service: "windows-work-browser-agent" });
        return;
      }

      if (request.method === "GET" && request.url === "/tasks") {
        json(response, 200, { tasks: await queue.list() });
        return;
      }

      if (request.method === "POST" && request.url === "/tasks") {
        const input = await body(request);
        const intent: TaskIntent = {
          id: typeof input.id === "string" && input.id ? input.id : randomUUID(),
          goal: typeof input.goal === "string" ? input.goal : "",
          ...(Number.isInteger(input.tabId) ? { tabId: Number(input.tabId) } : {}),
          workspaceId: options.workspaceId ?? (typeof input.workspaceId === "string" ? input.workspaceId : "default"),
          source: input.source === "mcp" || input.source === "api" ? input.source : "extension",
          createdAt: new Date().toISOString(),
        };
        const accepted = await queue.enqueue(intent);
        json(response, 202, { accepted: true, task: accepted });
        return;
      }

      json(response, 404, { error: "Not found" });
    } catch (error) {
      json(response, 400, { error: error instanceof Error ? error.message : String(error) });
    }
  });

  return { server, queue };
}

export async function startLocalAgentServer(options: LocalAgentServerOptions): Promise<ReturnType<typeof createServer>> {
  if (options.port !== undefined && (!Number.isInteger(options.port) || options.port < 1024 || options.port > 65535)) {
    throw new Error("Port must be between 1024 and 65535.");
  }
  const { server } = createLocalAgentServer(options);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(options.port ?? 17321, "127.0.0.1", () => resolve());
  });
  return server;
}
