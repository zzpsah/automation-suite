import { chromium, type Browser, type BrowserContext, type Page } from "playwright-core";
import {
  assertBrowserAction,
  type BrowserAction,
  type BrowserController,
  type BrowserObservation,
  type BrowserSessionRef,
  type BrowserVerification,
} from "../agent/browser-control-contract";

export interface PlaywrightControllerOptions {
  cdpEndpoint: string;
  defaultTimeoutMs?: number;
}

/** Capability-scoped semantic browser executor for an existing Chromium instance. */
export class PlaywrightController implements BrowserController {
  private readonly endpoint: string;
  private readonly defaultTimeout: number;
  private browser?: Browser;
  private readonly sessions = new Map<string, { context: BrowserContext; page?: Page }>();

  constructor(options: PlaywrightControllerOptions) {
    this.endpoint = options.cdpEndpoint;
    this.defaultTimeout = options.defaultTimeoutMs ?? 30_000;
  }

  private async getContext(session: BrowserSessionRef): Promise<BrowserContext> {
    let entry = this.sessions.get(session.id);
    if (entry?.context) return entry.context;
    this.browser ??= await chromium.connectOverCDP(this.endpoint);
    const context = this.browser.contexts()[0] ?? await this.browser.newContext();
    const pages = context.pages();
    const selected = session.activeTabId ? pages.find((page) => page.url() && page.url() === session.activeTabId) : pages[0];
    this.sessions.set(session.id, { context, ...(selected ? { page: selected } : {}) });
    return context;
  }

  private async getPage(session: BrowserSessionRef): Promise<Page> {
    const context = await this.getContext(session);
    const entry = this.sessions.get(session.id);
    const pages = context.pages();
    const page = entry?.page && !entry.page.isClosed() ? entry.page : pages[0] ?? await context.newPage();
    this.sessions.set(session.id, { context, page });
    return page;
  }

  private timeout(action: BrowserAction): number {
    return Math.min(300_000, Math.max(0, action.timeoutMs ?? this.defaultTimeout));
  }

  async observe(session: BrowserSessionRef): Promise<BrowserObservation> {
    const context = await this.getContext(session);
    const pages = context.pages();
    const active = pages[0];
    return {
      sessionId: session.id,
      url: active?.url() ?? "about:blank",
      ...(active ? { title: await active.title().catch(() => undefined) } : {}),
      tabs: pages.map((page, index) => ({
        id: String(index),
        url: page.url(),
        title: undefined,
        active: page === active,
      })),
      capturedAt: new Date().toISOString(),
    };
  }

  async act(action: BrowserAction): Promise<{ ok: boolean; detail?: string }> {
    assertBrowserAction(action);
    if (action.executor !== "playwright") {
      return { ok: false, detail: "PlaywrightController only accepts Playwright actions." };
    }
    const page = await this.getPage({ id: action.sessionId, profileId: "default" });
    const timeout = this.timeout(action);
    try {
      switch (action.operation) {
        case "navigate":
          if (!action.value) throw new Error("navigate requires value URL");
          await page.goto(action.value, { waitUntil: "domcontentloaded", timeout });
          return { ok: true, detail: page.url() };
        case "click":
          if (!action.target) throw new Error("click requires target selector");
          await page.locator(action.target).first().click({ timeout });
          return { ok: true };
        case "type":
          if (!action.target) throw new Error("type requires target selector");
          await page.locator(action.target).first().fill(action.value ?? "", { timeout });
          return { ok: true };
        case "select":
          if (!action.target || action.value === undefined) throw new Error("select requires target and value");
          await page.locator(action.target).first().selectOption(action.value, { timeout });
          return { ok: true };
        case "upload":
          if (!action.target || !action.value) throw new Error("upload requires input selector and path");
          await page.locator(action.target).first().setInputFiles(action.value, { timeout });
          return { ok: true };
        case "download": {
          const downloadPromise = page.waitForEvent("download", { timeout });
          if (!action.target) throw new Error("download requires clickable selector");
          await page.locator(action.target).first().click({ timeout });
          const download = await downloadPromise;
          return { ok: true, detail: await download.suggestedFilename() };
        }
        case "extract": {
          const selector = action.target ?? "body";
          const text = await page.locator(selector).first().innerText({ timeout });
          return { ok: true, detail: text.slice(0, 100_000) };
        }
        case "new-tab": {
          const newPage = await page.context().newPage();
          if (action.value) await newPage.goto(action.value, { waitUntil: "domcontentloaded", timeout });
          this.sessions.set(action.sessionId, { context: page.context(), page: newPage });
          return { ok: true, detail: newPage.url() };
        }
        case "switch-tab": {
          if (!action.target) throw new Error("switch-tab requires tab id");
          const index = Number(action.target);
          const pages = page.context().pages();
          if (!Number.isInteger(index) || index < 0 || index >= pages.length) throw new Error("Invalid tab index");
          this.sessions.set(action.sessionId, { context: page.context(), page: pages[index] });
          return { ok: true, detail: pages[index].url() };
        }
        case "wait":
          await page.waitForTimeout(Math.min(timeout, Number(action.value ?? 250)));
          return { ok: true };
      }
    } catch (error) {
      return { ok: false, detail: error instanceof Error ? error.message : String(error) };
    }
  }

  async verify(condition: BrowserVerification): Promise<{ passed: boolean; detail: string }> {
    const page = await this.getPage({ id: condition.sessionId, profileId: "default" });
    const timeout = this.defaultTimeout;
    try {
      switch (condition.condition) {
        case "url":
          return { passed: condition.expected === page.url(), detail: `Observed URL: ${page.url()}` };
        case "title": {
          const title = await page.title();
          return { passed: condition.expected === title, detail: `Observed title: ${title}` };
        }
        case "element-visible": {
          if (!condition.target) return { passed: false, detail: "Missing selector." };
          const visible = await page.locator(condition.target).first().isVisible({ timeout });
          return { passed: visible, detail: visible ? "Element is visible." : "Element is not visible." };
        }
        case "element-text": {
          if (!condition.target) return { passed: false, detail: "Missing selector." };
          const text = await page.locator(condition.target).first().innerText({ timeout });
          return { passed: condition.expected === text, detail: `Observed text: ${text.slice(0, 1000)}` };
        }
        case "tab-opened": {
          const count = page.context().pages().length;
          return { passed: count > 0, detail: `Observed tabs: ${count}` };
        }
        case "download-created":
          return { passed: false, detail: "Download verification requires a task-scoped download sink." };
        case "custom-observation":
          return { passed: false, detail: "Custom observation is not implemented by the Playwright adapter." };
      }
    } catch (error) {
      return { passed: false, detail: error instanceof Error ? error.message : String(error) };
    }
  }

  async close(): Promise<void> {
    this.sessions.clear();
    if (this.browser) await this.browser.close().catch(() => undefined);
    this.browser = undefined;
  }
}
