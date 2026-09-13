import type {
  BrowserAction,
  BrowserController,
  BrowserObservation,
  BrowserSessionRef,
  BrowserVerification,
} from "../agent/browser-control-contract.js";

interface CdpTarget {
  id: string;
  type?: string;
  title?: string;
  url: string;
  webSocketDebuggerUrl?: string;
}

export interface CdpAdapterOptions {
  host?: string;
  port: number;
  fetchImpl?: typeof fetch;
}

/**
 * Minimal Chromium DevTools Protocol discovery adapter. It deliberately uses
 * the browser's local debugging endpoint only; DOM/action execution belongs
 * behind a Playwright/Open Browser Use executor.
 */
export class CdpAdapter implements BrowserController {
  private readonly host: string;
  private readonly port: number;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CdpAdapterOptions) {
    this.host = options.host ?? "127.0.0.1";
    this.port = options.port;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private async json<T>(path: string): Promise<T> {
    const response = await this.fetchImpl(`http://${this.host}:${this.port}${path}`);
    if (!response.ok) throw new Error(`CDP HTTP ${response.status} for ${path}`);
    return (await response.json()) as T;
  }

  async observe(session: BrowserSessionRef): Promise<BrowserObservation> {
    const targets = await this.json<CdpTarget[]>("/json/list");
    const tabs = targets
      .filter((target) => target.type === "page")
      .map((target) => ({
        id: target.id,
        url: target.url,
        ...(target.title !== undefined ? { title: target.title } : {}),
        active: target.id === session.activeTabId,
      }));
    const active = tabs.find((tab) => tab.active) ?? tabs[0];
    return {
      sessionId: session.id,
      url: active?.url ?? "about:blank",
      ...(active?.title !== undefined ? { title: active.title } : {}),
      tabs,
      capturedAt: new Date().toISOString(),
    };
  }

  async act(action: BrowserAction): Promise<{ ok: boolean; detail?: string }> {
    if (action.executor !== "cdp") {
      return { ok: false, detail: "CdpAdapter only accepts CDP actions." };
    }
    // Low-level protocol operations are intentionally not exposed here.
    // Playwright/open-browser-use is responsible for semantic DOM actions.
    return { ok: false, detail: `Unsupported direct CDP operation: ${action.operation}` };
  }

  async verify(condition: BrowserVerification): Promise<{ passed: boolean; detail: string }> {
    const targets = await this.json<CdpTarget[]>("/json/list");
    const pages = targets.filter((target) => target.type === "page");
    if (condition.condition === "tab-opened") {
      const passed = condition.target ? pages.some((page) => page.id === condition.target) : pages.length > 0;
      return { passed, detail: passed ? "Expected page target observed." : "Expected page target not observed." };
    }
    if (condition.condition === "url") {
      const passed = condition.expected ? pages.some((page) => page.url === condition.expected) : false;
      return { passed, detail: passed ? "Expected URL observed." : "Expected URL not observed." };
    }
    return { passed: false, detail: `Verification '${condition.condition}' requires a semantic browser executor.` };
  }
}
