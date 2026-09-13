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
        case "mouse": {
          const x = Number(request.arguments.x);
          const y = Number(request.arguments.y);
          if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0 || x > 10000 || y > 10000) {
            return { ok: false, observation: {}, error: { code: "INVALID_COORDINATES", message: "Mouse coordinates are outside the supported range.", recoverable: false } };
          }
          const button = request.arguments.button === "right" ? "right" : "left";
          const script = `
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class WWBMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
}
'@
[WWBMouse]::SetCursorPos([int]$env:WWB_X, [int]$env:WWB_Y) | Out-Null
$down = if($env:WWB_BUTTON -eq 'right'){0x0008}else{0x0002}
$up = if($env:WWB_BUTTON -eq 'right'){0x0010}else{0x0004}
[WWBMouse]::mouse_event($down,0,0,0,[UIntPtr]::Zero)
[WWBMouse]::mouse_event($up,0,0,0,[UIntPtr]::Zero)
`;
          await powershell(script, { ...process.env, WWB_X: String(x), WWB_Y: String(y), WWB_BUTTON: button });
          return { ok: true, observation: {} };
        }
        case "file-dialog":
          return { ok: false, observation: {}, error: { code: "NOT_IMPLEMENTED", message: "File dialog automation requires a dialog-specific UI Automation adapter.", recoverable: true } };
        case "print": {
          const printPath = boundedText(request.arguments.path, 2048);
          if (!printPath) return { ok: false, observation: {}, error: { code: "MISSING_PATH", message: "print requires a file path.", recoverable: false } };
          await powershell("Start-Process -FilePath $env:WWB_PRINT_PATH -Verb Print", { ...process.env, WWB_PRINT_PATH: printPath });
          return { ok: true, observation: {} };
        }
      }
    } catch (error) {
      return { ok: false, observation: {}, error: { code: "NATIVE_EXECUTION_FAILED", message: error instanceof Error ? error.message : String(error), recoverable: true } };
    }
  }
}
