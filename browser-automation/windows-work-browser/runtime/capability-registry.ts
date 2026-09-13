import type { Capability, AutomationAction } from "../agent/action-contract.js";
import type { Executor } from "../agent/executor-contract.js";

export interface RegisteredCapability {
  capability: Capability;
  description: string;
  defaultRisk: "read" | "write" | "destructive" | "sensitive";
  executorKind: Executor["kind"];
}

export const CAPABILITIES: ReadonlyArray<RegisteredCapability> = [
  { capability: "browser.read", description: "Observe browser state", defaultRisk: "read", executorKind: "cdp" },
  { capability: "browser.navigate", description: "Navigate browser", defaultRisk: "read", executorKind: "playwright" },
  { capability: "browser.click", description: "Click semantic web controls", defaultRisk: "read", executorKind: "playwright" },
  { capability: "browser.type", description: "Enter text into web controls", defaultRisk: "write", executorKind: "playwright" },
  { capability: "browser.upload", description: "Upload a prepared file", defaultRisk: "sensitive", executorKind: "playwright" },
  { capability: "browser.download", description: "Download a browser resource", defaultRisk: "write", executorKind: "playwright" },
  { capability: "browser.extract", description: "Extract structured page data", defaultRisk: "read", executorKind: "playwright" },
  { capability: "desktop.observe", description: "Observe native window state", defaultRisk: "read", executorKind: "windows-native" },
  { capability: "desktop.keyboard", description: "Perform approved keyboard action", defaultRisk: "write", executorKind: "windows-native" },
  { capability: "desktop.mouse", description: "Perform approved mouse action", defaultRisk: "write", executorKind: "windows-native" },
  { capability: "desktop.window", description: "Activate or inspect an approved window", defaultRisk: "write", executorKind: "windows-native" },
  { capability: "desktop.clipboard", description: "Read or write clipboard through policy", defaultRisk: "sensitive", executorKind: "windows-native" },
  { capability: "desktop.file_dialog", description: "Operate a native file dialog", defaultRisk: "write", executorKind: "windows-native" },
  { capability: "desktop.print", description: "Print through native/browser dialog", defaultRisk: "sensitive", executorKind: "windows-native" },
  { capability: "files.read", description: "Read a permitted file", defaultRisk: "read", executorKind: "service" },
  { capability: "files.write", description: "Write a permitted file", defaultRisk: "write", executorKind: "service" },
  { capability: "files.delete", description: "Delete a file", defaultRisk: "destructive", executorKind: "service" },
  { capability: "pdf.process", description: "Run a PDF operation", defaultRisk: "write", executorKind: "service" },
  { capability: "image.process", description: "Run an image operation", defaultRisk: "write", executorKind: "service" },
  { capability: "communication.send", description: "Send an external message", defaultRisk: "sensitive", executorKind: "service" },
] as const;

export function findCapability(capability: Capability): RegisteredCapability {
  const item = CAPABILITIES.find((candidate) => candidate.capability === capability);
  if (!item) throw new Error(`Capability is not registered: ${capability}`);
  return item;
}

export function normalizeActionRisk(action: AutomationAction): AutomationAction {
  const registered = findCapability(action.capability);
  if (action.risk !== registered.defaultRisk) {
    return { ...action, risk: action.risk };
  }
  return action;
}
