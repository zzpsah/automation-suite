export type Capability =
  | "browser.read"
  | "browser.navigate"
  | "browser.click"
  | "browser.type"
  | "browser.upload"
  | "browser.download"
  | "browser.extract"
  | "desktop.observe"
  | "desktop.keyboard"
  | "desktop.mouse"
  | "desktop.window"
  | "desktop.clipboard"
  | "desktop.file_dialog"
  | "desktop.print"
  | "files.read"
  | "files.write"
  | "files.delete"
  | "pdf.process"
  | "image.process"
  | "communication.send";

export type Risk = "read" | "write" | "destructive" | "sensitive";

export interface AutomationAction {
  id: string;
  capability: Capability;
  risk: Risk;
  target?: string;
  args: Record<string, unknown>;
  requiresApproval: boolean;
  reason: string;
}

export interface ActionResult {
  actionId: string;
  ok: boolean;
  output?: unknown;
  evidence?: Array<{ type: string; value: string }>;
  error?: { code: string; message: string; recoverable: boolean };
}

/**
 * The model never receives direct access to Playwright, AHK, PowerShell or
 * arbitrary native execution. It produces validated AutomationAction values.
 * Executors are selected by the orchestrator and every result is verified.
 */
export function requiresApproval(action: AutomationAction): boolean {
  return action.requiresApproval || action.risk === "destructive" || action.risk === "sensitive";
}
