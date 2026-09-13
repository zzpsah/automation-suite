import type { ActionResult, AutomationAction } from "../agent/action-contract.js";
import type { ExecutionContext, Executor } from "../agent/executor-contract.js";

export interface SemanticPage {
  goto(url: string, options?: { timeout?: number }): Promise<unknown>;
  getByRole(role: string, options?: { name?: string }): SemanticLocator;
  locator(selector: string): SemanticLocator;
  title(): Promise<string>;
  url(): string;
}

export interface SemanticLocator {
  click(options?: { timeout?: number }): Promise<void>;
  fill(value: string, options?: { timeout?: number }): Promise<void>;
  selectOption(value: string, options?: { timeout?: number }): Promise<unknown>;
  setInputFiles(path: string, options?: { timeout?: number }): Promise<void>;
  textContent(): Promise<string | null>;
  isVisible(): Promise<boolean>;
}

export interface BrowserPageFactory {
  getPage(context: ExecutionContext): Promise<SemanticPage>;
}

/**
 * Playwright-compatible semantic executor. The concrete browser package can
 * inject a real Playwright Page without making this agent package depend on a
 * particular Playwright version.
 */
export class PlaywrightExecutor implements Executor {
  readonly kind = "playwright" as const;

  constructor(private readonly pages: BrowserPageFactory) {}

  supports(action: AutomationAction): boolean {
    return action.capability.startsWith("browser.") && action.capability !== "browser.read";
  }

  async execute(action: AutomationAction, context: ExecutionContext): Promise<ActionResult> {
    const page = await this.pages.getPage(context);
    try {
      const target = typeof action.target === "string" ? action.target : undefined;
      const args = action.args;
      switch (action.capability) {
        case "browser.navigate":
          if (!target) throw new Error("navigate requires target URL");
          await page.goto(target, { timeout: numberArg(args.timeoutMs) });
          return ok(action.id, `Navigated to ${page.url()}`);
        case "browser.click":
          await locatorFor(page, target, args).click({ timeout: numberArg(args.timeoutMs) });
          return ok(action.id, "Clicked target");
        case "browser.type":
          await locatorFor(page, target, args).fill(stringArg(args.text));
          return ok(action.id, "Filled target");
        case "browser.download":
          throw new Error("Download executor requires the concrete Playwright download handler.");
        case "browser.upload":
          await locatorFor(page, target, args).setInputFiles(stringArg(args.filePath));
          return ok(action.id, "Uploaded prepared file");
        case "browser.extract":
          return ok(action.id, await locatorFor(page, target, args).textContent());
        default:
          throw new Error(`Unsupported browser capability: ${action.capability}`);
      }
    } catch (error) {
      return {
        actionId: action.id,
        ok: false,
        error: {
          code: "PLAYWRIGHT_EXECUTION_FAILED",
          message: error instanceof Error ? error.message : String(error),
          recoverable: true,
        },
      };
    }
  }
}

function stringArg(value: unknown): string {
  if (typeof value !== "string" || value.length === 0) throw new Error("Required string argument missing.");
  return value;
}

function numberArg(value: unknown): number | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) throw new Error("Invalid timeout.");
  return value;
}

function locatorFor(page: SemanticPage, target: string | undefined, args: Record<string, unknown>): SemanticLocator {
  if (typeof target !== "string" || target.length === 0) throw new Error("Browser action requires a target.");
  if (typeof args.role === "string") return page.getByRole(args.role, typeof args.name === "string" ? { name: args.name } : undefined);
  return page.locator(target);
}

function ok(actionId: string, output: unknown): ActionResult {
  return { actionId, ok: true, output };
}
