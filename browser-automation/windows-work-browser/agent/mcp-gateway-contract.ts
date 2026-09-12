import { AutomationAction, Capability } from "./action-contract";

export interface McpCapability {
  name: string;
  capability: Capability;
  description: string;
  requiresApproval: boolean;
}

export interface McpRequest {
  requestId: string;
  workspaceId: string;
  capability: Capability;
  arguments: Record<string, unknown>;
}

export interface McpResponse {
  requestId: string;
  ok: boolean;
  action?: AutomationAction;
  result?: unknown;
  error?: { code: string; message: string };
}

/**
 * MCP is a capability gateway, not a generic command runner. Implementations
 * must map requests to declared AutomationAction values before execution.
 */
export interface McpGateway {
  listCapabilities(): Promise<ReadonlyArray<McpCapability>>;
  authorize(request: McpRequest): Promise<AutomationAction>;
}
