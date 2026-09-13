export interface BrowserTarget {
  id: string;
  url: string;
  title?: string;
  type?: string;
}

export interface BrowserControl {
  listTargets(): Promise<ReadonlyArray<BrowserTarget>>;
  navigate(targetId: string, url: string): Promise<void>;
  click(targetId: string, selector: string): Promise<void>;
  fill(targetId: string, selector: string, value: string): Promise<void>;
  select(targetId: string, selector: string, value: string): Promise<void>;
  upload(targetId: string, selector: string, pathToken: string): Promise<void>;
  download(targetId: string, url: string): Promise<{ path: string; sha256: string }>;
  extract(targetId: string, selectors: Record<string, string>): Promise<Record<string, string>>;
  screenshot(targetId: string): Promise<{ reference: string; sha256: string }>;
}

export interface ExistingBrowserBridge {
  connect(endpoint: string): Promise<BrowserControl>;
  isAvailable(): Promise<boolean>;
}

/**
 * Browser control is intentionally expressed as bounded semantic operations.
 * Runtime implementations may delegate to Playwright, CDP, or open-browser-use.
 */
