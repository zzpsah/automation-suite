export type McpTransport = "stdio" | "http" | "websocket";

export interface McpServerDescriptor {
  id: string;
  name: string;
  transport: McpTransport;
  endpoint?: string;
  enabled: boolean;
  allowedCapabilities: string[];
}

export interface McpToolDescriptor {
  serverId: string;
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  capabilities: string[];
}

export interface McpToolCall {
  requestId: string;
  serverId: string;
  tool: string;
  arguments: Record<string, unknown>;
  requestedCapabilities: string[];
}

export interface McpToolResult {
  requestId: string;
  ok: boolean;
  content: unknown;
  error?: { code: string; message: string };
}

/**
 * MCP is an integration boundary, not an execution bypass. A gateway must
 * translate tool calls into AutomationAction values and run the same policy,
 * approval, execution, and verification pipeline as first-party tasks.
 */
export interface McpGateway {
  listServers(): Promise<McpServerDescriptor[]>;
  listTools(serverId: string): Promise<McpToolDescriptor[]>;
  callTool(call: McpToolCall): Promise<McpToolResult>;
}

export function assertMcpCallAllowed(
  server: McpServerDescriptor,
  call: McpToolCall,
): void {
  if (!server.enabled) throw new Error(`MCP server is disabled: ${server.id}`);
  if (server.id !== call.serverId) throw new Error("MCP server identity mismatch.");

  for (const capability of call.requestedCapabilities) {
    if (!server.allowedCapabilities.includes(capability)) {
      throw new Error(`MCP capability is not allowed: ${capability}`);
    }
  }
}
