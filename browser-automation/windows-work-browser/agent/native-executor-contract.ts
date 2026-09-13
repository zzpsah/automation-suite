import { ActionResult, AutomationAction } from "./action-contract";
import { ExecutionContext, Executor } from "./executor-contract";

/**
 * Narrow Windows-native adapter boundary.
 *
 * The implementation may use Win32/UI Automation/AutoHotkey, but the model is
 * never given an arbitrary command line, script body, executable path, or
 * interpreter channel. Every operation arrives as a typed AutomationAction.
 */
export type NativeOperation =
  | "observe.window"
  | "keyboard.press"
  | "keyboard.type"
  | "mouse.click"
  | "window.activate"
  | "clipboard.read"
  | "clipboard.write"
  | "file-dialog.open"
  | "file-dialog.save"
  | "print.dialog";

export interface NativeActionArgs {
  operation: NativeOperation;
  targetWindow?: string;
  text?: string;
  key?: string;
  x?: number;
  y?: number;
  pathToken?: string;
}

export interface NativeExecutor extends Executor {
  readonly kind: "windows-native";
  executeNative(
    action: AutomationAction,
    args: NativeActionArgs,
    context: ExecutionContext,
  ): Promise<ActionResult>;
}

export function isNativeCapability(action: AutomationAction): boolean {
  return action.capability.startsWith("desktop.");
}

/** Rejects an action before it reaches a native adapter. */
export function assertNativeActionShape(action: AutomationAction): NativeActionArgs {
  if (!isNativeCapability(action)) {
    throw new Error(`Native executor cannot handle capability: ${action.capability}`);
  }

  const args = action.args as Partial<NativeActionArgs>;
  if (typeof args.operation !== "string") {
    throw new Error("Native action requires a declared operation.");
  }

  return args as NativeActionArgs;
}
