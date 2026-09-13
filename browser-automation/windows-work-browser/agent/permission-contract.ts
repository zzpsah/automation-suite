import { Capability, Risk } from "./action-contract";

export type ApprovalDecision = "allow" | "deny" | "allow-once";

export interface WorkspacePermission {
  workspaceId: string;
  capability: Capability;
  risk: Risk;
  decision: ApprovalDecision;
  expiresAt?: string;
  reason: string;
}

export interface ApprovalRequest {
  requestId: string;
  taskId: string;
  actionId: string;
  capability: Capability;
  risk: Risk;
  summary: string;
  target?: string;
}

export interface PermissionCenter {
  get(workspaceId: string, capability: Capability): Promise<WorkspacePermission | undefined>;
  requestApproval(request: ApprovalRequest): Promise<ApprovalDecision>;
  revoke(workspaceId: string, capability: Capability): Promise<void>;
}

export function requiresExplicitApproval(risk: Risk, capability: Capability): boolean {
  return (
    risk === "destructive" ||
    risk === "sensitive" ||
    capability === "communication.send" ||
    capability === "browser.upload" ||
    capability === "desktop.print"
  );
}
