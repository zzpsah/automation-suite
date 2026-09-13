import { evaluateAction } from "../agent/policy-engine";
import type { AutomationAction, Capability } from "../agent/action-contract";
import type { McpCapability, McpGateway, McpRequest } from "../agent/mcp-gateway-contract";

const CAPABILITIES: ReadonlyArray<McpCapability> = [
  { name: "browser.navigate", capability: "browser.navigate", description: "Navigate the active browser tab.", requiresApproval: false },
  { name: "browser.click", capability: "browser.click", description: "Click a declared browser target.", requiresApproval: false },
  { name: "browser.type", capability: "browser.type", description: "Fill a declared browser input.", requiresApproval: false },
  { name: "browser.extract", capability: "browser.extract", description: "Read bounded page content.", requiresApproval: false },
  { name: "browser.upload", capability: "browser.upload", description: "Upload a user-selected file into a page input.", requiresApproval: true },
  { name: "browser.download", capability: "browser.download", description: "Trigger a page download.", requiresApproval: true },
  { name: "files.read", capability: "files.read", description: "Read an approved workspace file.", requiresApproval: false },
  { name: "files.write", capability: "files.write", description: "Write an approved workspace file.", requiresApproval: true },
  { name: "files.delete", capability: "files.delete", description: "Delete an approved workspace file.", requiresApproval: true },
  { name: "communication.send", capability: "communication.send", description: "Send an outbound communication.", requiresApproval: true },
];

function safeId(prefix: string, requestId: string): string {
  return `${prefix}-${requestId.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 80)}`;
}

/** MCP implementation that can only emit declared AutomationAction values. */
export class DeterministicMcpGateway implements McpGateway {
  async listCapabilities(): Promise<ReadonlyArray<McpCapability>> {
    return CAPABILITIES;
  }

  async authorize(request: McpRequest): Promise<AutomationAction> {
    const declared = CAPABILITIES.find((capability) => capability.capability === request.capability);
    if (!declared) throw new Error(`Unsupported MCP capability: ${request.capability}`);

    const risk = (request.arguments.risk as AutomationAction["risk"] | undefined) ?? (declared.requiresApproval ? "sensitive" : "read");
    const action: AutomationAction = {
      id: safeId("mcp", request.requestId),
      capability: request.capability,
      risk,
      ...(typeof request.arguments.target === "string" ? { target: request.arguments.target } : {}),
      args: { ...request.arguments },
      requiresApproval: declared.requiresApproval || risk === "destructive" || risk === "sensitive",
      reason: `MCP request ${request.requestId}`,
    };
    const decision = evaluateAction(action);
    if (!decision.allowed) throw new Error(decision.reason);
    return action;
  }
}

export function isDeclaredCapability(value: string): value is Capability {
  return CAPABILITIES.some((capability) => capability.capability === value);
}
