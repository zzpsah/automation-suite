export type DesktopOperation =
  | "observe-window"
  | "activate-window"
  | "press-key"
  | "type-text"
  | "click"
  | "clipboard-read"
  | "clipboard-write"
  | "open-file-dialog"
  | "save-file-dialog"
  | "print";

export interface DesktopAction {
  operation: DesktopOperation;
  windowTitle?: string;
  key?: string;
  text?: string;
  x?: number;
  y?: number;
  pathToken?: string;
}

export interface DesktopObservation {
  foregroundWindow?: string;
  clipboardFormat?: string;
  activeControl?: string;
}

export interface DesktopControl {
  observe(): Promise<DesktopObservation>;
  execute(action: DesktopAction): Promise<void>;
}

/**
 * Runtime implementations may use Win32/UI Automation and AutoHotkey. They
 * must translate only the declared operations; arbitrary interpreter/shell
 * invocation is deliberately outside this contract.
 */
