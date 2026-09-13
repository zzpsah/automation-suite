import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { NativeObservation, NativeRequest, NativeResult, WindowsNativeExecutor } from "../agent/windows-native-contract";

const execFileAsync = promisify(execFile);
const POWERSHELL = "powershell.exe";

function requireWindows(): void {
  if (process.platform !== "win32") throw new Error("Windows native executor requires Windows.");
}

function boundedText(value: unknown, max = 4000): string {
  return typeof value === "string" ? value.slice(0, max) : "";
}

async function powershell(script: string, environment: NodeJS.ProcessEnv): Promise<string> {
  const { stdout } = await execFileAsync(POWERSHELL, ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], {
    windowsHide: true,
    timeout: 15_000,
    env: environment,
    maxBuffer: 1024 * 1024,
  });
  return stdout.trim();
}

/** Fixed-operation Windows adapter. It never accepts a shell/script payload from the caller. */
export class FixedWindowsNativeExecutor implements WindowsNativeExecutor {
  async observe(): Promise<NativeObservation> {
    requireWindows();
    const output = await powershell(`
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class WWBUser32 {
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@
$h = [WWBUser32]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 512
[void][WWBUser32]::GetWindowText($h, $sb, $sb.Capacity)
$pid = 0
[void][WWBUser32]::GetWindowThreadProcessId($h, [ref]$pid)
$p = if ($pid -gt 0) { Get-Process -Id $pid -ErrorAction SilentlyContinue } else { $null }
[ordered]@{title=$sb.ToString(); process=if($p){$p.ProcessName}else{$null}} | ConvertTo-Json -Compress
`, process.env);
    const parsed = JSON.parse(output || "{}") as { title?: string; process?: string };
    return { foregroundWindow: { title: parsed.title ?? "", ...(parsed.process ? { process: parsed.process } : {}) } };
  }

  async execute(request: NativeRequest): Promise<NativeResult> {
    requireWindows();
    if (!Number.isInteger(request.timeoutMs) || request.timeoutMs < 1 || request.timeoutMs > 120_000) {
      return { ok: false, observation: {}, error: { code: "INVALID_TIMEOUT", message: "timeoutMs is outside the supported range.", recoverable: false } };
    }
    try {
      switch (request.operation) {
        case "clipboard-read":
          await powershell("Get-Clipboard -Raw | Out-Null", process.env);
          return { ok: true, observation: { clipboardChanged: false } };
        case "clipboard-write": {
          const text = boundedText(request.arguments.text);
          await powershell("Set-Clipboard -Value $env:WWB_CLIPBOARD", { ...process.env, WWB_CLIPBOARD: text });
          return { ok: true, observation: { clipboardChanged: true } };
        }
        case "activate-window": {
          const title = boundedText(request.targetWindow?.title, 512);
          const processName = boundedText(request.targetWindow?.process, 128);
          if (!title && !processName) return { ok: false, observation: {}, error: { code: "MISSING_TARGET", message: "Window title or process is required.", recoverable: false } };
          const result = await powershell(`
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class WWBUser32 { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); }
'@
$targetTitle=$env:WWB_TITLE; $targetProcess=$env:WWB_PROCESS
$procs=@()
if($targetProcess){$procs+=Get-Process -Name $targetProcess -ErrorAction SilentlyContinue}
if($targetTitle){$procs+=Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*$targetTitle*"}}
$p=$procs | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1
if(-not $p){throw "Target window not found."}
[WWBUser32]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
$p.Id
`, { ...process.env, WWB_TITLE: title, WWB_PROCESS: processName });
          return { ok: true, observation: { foregroundWindow: { title: title || result, ...(processName ? { process: processName } : {}) } } };
        }
        case "keyboard": {
          const keys = boundedText(request.arguments.keys, 1000);
          if (!keys) return { ok: false, observation: {}, error: { code: "MISSING_KEYS", message: "keyboard requires a keys string.", recoverable: false } };
          await powershell("(New-Object -ComObject WScript.Shell).SendKeys($env:WWB_KEYS)", { ...process.env, WWB_KEYS: keys });
          return { ok: true, observation: {} };
        }
        case "mouse":
        case "file-dialog":
        case "print":
          return { ok: false, observation: {}, error: { code: "NOT_IMPLEMENTED", message: `Native operation '${request.operation}' requires a dedicated bounded adapter implementation.`, recoverable: true } };
      }
    } catch (error) {
      return { ok: false, observation: {}, error: { code: "NATIVE_EXECUTION_FAILED", message: error instanceof Error ? error.message : String(error), recoverable: true } };
    }
  }
}
