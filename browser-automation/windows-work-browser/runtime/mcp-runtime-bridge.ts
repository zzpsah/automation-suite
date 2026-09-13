import type { AutomationAction } from "../agent/action-contract";
import { evaluateAction } from "../agent/policy-engine";
import { DeterministicMcpGateway } from "./mcp-gateway";
import { PlaywrightController } from "./playwright-controller";

export interface McpExecutionResult {
  ok: boolean;
  status: "executed" | "approval_required" | "denied" | "failed";
  action: AutomationAction;
  output?: string;
  error?: string;
}

function browserOperation(capability: AutomationAction["capability"]): string | undefined {
  const map: Record<string, string> = {
    "browser.navigate": "navigate",
    "browser.click": "click",
    "browser.type": "type",
    "browser.extract": "extract",
    "browser.upload": "upload",
    "browser.download": "download",
  };
  return map[capability];
}

/** MCP execution bridge. Only declared browser capabilities are executable here. */
export class McpRuntimeBridge {
  constructor(
    private readonly gateway = new DeterministicMcpGateway(),
    private readonly browser?: PlaywrightController,
  ) {}

  async execute(request: Parameters<DeterministicMcpGateway["authorize"]>[0]): Promise<McpExecutionResult> {
    const action = await this.gateway.authorize(request);
    const decision = evaluateAction(action);
    if (!decision.allowed) return { ok: false, status: "denied", action, error: decision.reason };
    if (decision.requiresApproval) return { ok: false, status: "approval_required", action };

    const operation = browserOperation(action.capability);
    if (!operation) {
      return { ok: false, status: "failed", action, error: `No runtime executor for MCP capability: ${action.capability}` };
    }
    if (!this.browser) return { ok: false, status: "failed", action, error: "Browser runtime is not connected." };

    const args = action.args;
    const sessionId = typeof args.sessionId === "string" ? args.sessionId : request.workspaceId;
    const result = await this.browser.act({
      sessionId,
      executor: "playwright",
      operation: operation as "navigate" | "click" | "type" | "extract" | "upload" | "download",
      ...(typeof args.target === "string" ? { target: args.target } : {}),
      ...(typeof args.value === "string" ? { value: args.value } : {}),
      ...(Number.isInteger(args.timeoutMs) ? { timeoutMs: Number(args.timeoutMs) } : {}),
    });
    return result.ok
      ? { ok: true, status: "executed", action, ...(result.detail ? { output: result.detail } : {}) }
      : { ok: false, status: "failed", action, error: result.detail ?? "Browser execution failed." };
  }
}
