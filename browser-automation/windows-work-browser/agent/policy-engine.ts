import { AutomationAction, Risk, requiresApproval } from "./action-contract";

export type PolicyDecision =
  | { allowed: true; requiresApproval: boolean; reason: string }
  | { allowed: false; requiresApproval: true; reason: string };

const APPROVAL_REQUIRED_RISKS: Risk[] = ["destructive", "sensitive"];
const APPROVAL_REQUIRED_CAPABILITIES = new Set<AutomationAction["capability"]>([
  "communication.send",
  "browser.upload",
  "desktop.print",
]);

/**
 * Deterministic policy gate between an AI plan and an executor.
 * External side effects are approval-bound even if a malformed caller claims
 * otherwise in the action payload.
 */
export function evaluateAction(action: AutomationAction): PolicyDecision {
  if (!action.id || !action.reason) {
    return { allowed: false, requiresApproval: true, reason: "Action id and reason are mandatory." };
  }

  if (APPROVAL_REQUIRED_RISKS.includes(action.risk)) {
    return {
      allowed: true,
      requiresApproval: true,
      reason: `Risk level '${action.risk}' requires human approval before execution.`,
    };
  }

  if (APPROVAL_REQUIRED_CAPABILITIES.has(action.capability)) {
    return {
      allowed: true,
      requiresApproval: true,
      reason: `Capability '${action.capability}' requires explicit approval before its external side effect.`,
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
