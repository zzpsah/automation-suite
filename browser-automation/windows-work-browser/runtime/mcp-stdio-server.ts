import * as readline from "node:readline";
import { DeterministicMcpGateway } from "./mcp-gateway";
import type { McpRequest } from "../agent/mcp-gateway-contract";

interface RpcRequest {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: Record<string, unknown>;
}

function send(id: string | number, result?: unknown, error?: { code: number; message: string }): void {
  const payload = error
    ? { jsonrpc: "2.0", id, error }
    : { jsonrpc: "2.0", id, result };
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

export async function handleRpc(gateway: DeterministicMcpGateway, request: RpcRequest): Promise<void> {
  try {
    switch (request.method) {
      case "initialize":
        send(request.id, {
          protocolVersion: "2025-06-18",
          serverInfo: { name: "windows-work-browser", version: "0.5.0" },
          capabilities: { tools: {} },
        });
        return;
      case "tools/list": {
        const capabilities = await gateway.listCapabilities();
        send(request.id, {
          tools: capabilities.map((capability) => ({
            name: capability.name,
            description: capability.description,
            inputSchema: { type: "object", additionalProperties: true },
          })),
        });
        return;
      }
      case "tools/call": {
        const params = request.params ?? {};
        const tool = typeof params.name === "string" ? params.name : "";
        const argumentsValue = params.arguments;
        if (!tool || !argumentsValue || typeof argumentsValue !== "object") {
          send(request.id, undefined, { code: -32602, message: "tools/call requires name and arguments." });
          return;
        }
        const capabilities = await gateway.listCapabilities();
        const declared = capabilities.find((capability) => capability.name === tool);
        if (!declared) {
          send(request.id, undefined, { code: -32601, message: `Unknown tool: ${tool}` });
          return;
        }
        const mcpRequest: McpRequest = {
          requestId: `stdio-${request.id}`,
          workspaceId: typeof (argumentsValue as Record<string, unknown>).workspaceId === "string"
            ? String((argumentsValue as Record<string, unknown>).workspaceId)
            : "stdio",
          capability: declared.capability,
          arguments: { ...(argumentsValue as Record<string, unknown>) },
        };
        const action = await gateway.authorize(mcpRequest);
        send(request.id, {
          content: [{ type: "text", text: JSON.stringify({ authorized: true, action }) }],
          isError: false,
        });
        return;
      }
      default:
        send(request.id, undefined, { code: -32601, message: `Method not found: ${request.method}` });
    }
  } catch (error) {
    send(request.id, undefined, { code: -32000, message: error instanceof Error ? error.message : String(error) });
  }
}

export async function runStdioServer(): Promise<void> {
  const gateway = new DeterministicMcpGateway();
  const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of input) {
    if (!line.trim()) continue;
    const request = JSON.parse(line) as RpcRequest;
    await handleRpc(gateway, request);
  }
}

if (require.main === module) {
  runStdioServer().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.stack ?? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
