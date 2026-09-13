export type BrowserExecutorKind = "playwright" | "cdp" | "open-browser-use";

export interface BrowserSessionRef {
  id: string;
  profileId: string;
  origin?: string;
  activeTabId?: string;
}

export interface BrowserObservation {
  sessionId: string;
  url: string;
  title?: string;
  tabs: Array<{ id: string; url: string; title?: string; active: boolean }>;
  elements?: Array<{
    id: string;
    role?: string;
    name?: string;
    selector?: string;
    editable?: boolean;
  }>;
  capturedAt: string;
}

export interface BrowserAction {
  sessionId: string;
  executor: BrowserExecutorKind;
  operation:
    | "navigate"
    | "click"
    | "type"
    | "select"
    | "upload"
    | "download"
    | "extract"
    | "new-tab"
    | "switch-tab"
    | "wait";
  target?: string;
  value?: string;
  timeoutMs?: number;
}

export interface BrowserVerification {
  sessionId: string;
  condition:
    | "url"
    | "title"
    | "element-visible"
    | "element-text"
    | "download-created"
    | "tab-opened"
    | "custom-observation";
  target?: string;
  expected?: string;
}

export interface BrowserController {
  observe(session: BrowserSessionRef): Promise<BrowserObservation>;
  act(action: BrowserAction): Promise<{ ok: boolean; detail?: string }>;
  verify(condition: BrowserVerification): Promise<{ passed: boolean; detail: string }>;
}

/** External browser-control adapters must remain capability-scoped. */
export function assertBrowserAction(action: BrowserAction): void {
  if (!action.sessionId || !action.operation) throw new Error("Browser action is incomplete.");
  if (action.operation === "upload" && !action.value) throw new Error("Upload requires a file token/path reference.");
  if (action.timeoutMs !== undefined && (action.timeoutMs < 0 || action.timeoutMs > 300_000)) {
    throw new Error("Browser action timeout is outside the supported bounds.");
  }
}
