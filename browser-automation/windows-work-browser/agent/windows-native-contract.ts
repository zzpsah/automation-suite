export type NativeOperation =
  | "activate-window"
  | "keyboard"
  | "mouse"
  | "clipboard-read"
  | "clipboard-write"
  | "file-dialog"
  | "print";

export interface NativeRequest {
  operation: NativeOperation;
  targetWindow?: { title?: string; process?: string };
  arguments: Record<string, unknown>;
  timeoutMs: number;
}

export interface NativeObservation {
  foregroundWindow?: { title: string; process?: string };
  clipboardChanged?: boolean;
  dialogVisible?: boolean;
}

export interface NativeResult {
  ok: boolean;
  observation: NativeObservation;
  error?: { code: string; message: string; recoverable: boolean };
}

export interface WindowsNativeExecutor {
  observe(): Promise<NativeObservation>;
  execute(request: NativeRequest): Promise<NativeResult>;
}

/** Concrete AHK/Win32 implementation belongs behind this boundary. */
