import { AutomationAction, Risk, requiresApproval } from "./action-contract";

export type PolicyDecision =
  | { allowed: true; requiresApproval: boolean; reason: string }
  | { allowed: false; requiresApproval: true; reason: string };

const DENIED_BY_DEFAULT: Risk[] = ["destructive", "sensitive"];

/**
 * Deterministic policy gate between an AI plan and an executor.
 * Unknown capabilities must be rejected by the caller's schema validation.
 */
export function evaluateAction(action: AutomationAction): PolicyDecision {
  if (!action.id || !action.reason) {
    return { allowed: false, requiresApproval: true, reason: "Action id and reason are mandatory." };
  }

  if (DENIED_BY_DEFAULT.includes(action.risk)) {
    return {
      allowed: true,
      requiresApproval: true,
      reason: `Risk level '${action.risk}' requires human approval before execution.`,
    };
  }

  if (action.capability === "communication.send" || action.capability === "browser.upload" || action.capability === "desktop.print") {
    return {
      allowed: true,
      requiresApproval: requiresApproval(action),
      reason: "External side effect requires an explicit policy decision/approval according to workspace policy.",
    };
  }

  return {
    allowed: true,
    requiresApproval: requiresApproval(action),
    reason: "Action is within the declared automation capability contract.",
  };
}

export function assertAllowed(action: AutomationAction): void {
  const decision = evaluateAction(action);
  if (!decision.allowed) throw new Error(decision.reason);
}
