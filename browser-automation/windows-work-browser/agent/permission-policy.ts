import { AutomationAction, Capability } from "./action-contract";

export const APPROVAL_REQUIRED: ReadonlySet<Capability> = new Set([
  "browser.upload",
  "communication.send",
  "desktop.print",
  "files.write",
  "files.delete",
]);

export const HUMAN_ONLY_BY_DEFAULT: ReadonlySet<Capability> = new Set([
  "files.delete",
]);

export function policyRequiresApproval(action: AutomationAction): boolean {
  return action.requiresApproval || APPROVAL_REQUIRED.has(action.capability) ||
    action.risk === "destructive" || action.risk === "sensitive";
}

export function isHumanOnlyByDefault(action: AutomationAction): boolean {
  return HUMAN_ONLY_BY_DEFAULT.has(action.capability);
}
