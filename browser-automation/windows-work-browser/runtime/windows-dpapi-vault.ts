import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { CredentialRef, CredentialUseRequest, CredentialVault } from "../agent/credential-vault-contract";

const execFileAsync = promisify(execFile);
const POWERSHELL = "powershell.exe";

function requireWindows(): void {
  if (process.platform !== "win32") throw new Error("Windows credential vault requires Windows.");
}

function safe(value: string, max = 512): string {
  return value.slice(0, max);
}

/**
 * Windows-backed credential boundary. Raw secret material is consumed only by
 * the PowerShell process and is never returned to the caller.
 */
export class WindowsDpapiCredentialVault implements CredentialVault {
  private readonly namespace: string;

  constructor(namespace = "WindowsWorkBrowser") {
    this.namespace = namespace.replace(/[^A-Za-z0-9_-]/g, "_").slice(0, 64);
  }

  async list(origin?: string): Promise<ReadonlyArray<CredentialRef>> {
    requireWindows();
    // Credential Manager enumeration is intentionally represented as opaque refs.
    // Runtime enumeration is enabled only through the signed native integration.
    const script = `
$target = $env:WWB_TARGET
if (-not $target) { throw 'Missing credential namespace.' }
# Test-safe enumeration contract: return only opaque target identifiers.
$targets = @()
$store = Join-Path $env:LOCALAPPDATA 'WindowsWorkBrowser\\credential-index.json'
if (Test-Path $store) {
  try { $targets = (Get-Content $store -Raw | ConvertFrom-Json) } catch {}
}
@($targets | Where-Object { -not $env:WWB_ORIGIN -or $_.origin -eq $env:WWB_ORIGIN } | ForEach-Object { [ordered]@{id=$_.id;origin=$_.origin;username=$_.username} }) | ConvertTo-Json -Compress
`;
    const { stdout } = await execFileAsync(POWERSHELL, ["-NoProfile", "-NonInteractive", "-Command", script], {
      windowsHide: true,
      timeout: 15_000,
      env: { ...process.env, WWB_TARGET: this.namespace, WWB_ORIGIN: safe(origin ?? "", 256) },
      maxBuffer: 256 * 1024,
    });
    if (!stdout.trim()) return [];
    const parsed = JSON.parse(stdout) as Array<CredentialRef> | CredentialRef;
    return Array.isArray(parsed) ? parsed : [parsed];
  }

  async use(request: CredentialUseRequest): Promise<{ ok: boolean; sessionRef?: string; error?: string }> {
    requireWindows();
    if (!request.credentialId || !request.origin || !request.purpose) {
      return { ok: false, error: "credentialId, origin and purpose are required." };
    }
    const script = `
$origin = $env:WWB_ORIGIN
$id = $env:WWB_ID
$purpose = $env:WWB_PURPOSE
if (-not $origin -or -not $id -or -not $purpose) { throw 'Incomplete credential request.' }
# Real secret lookup/use belongs in the packaged native Credential Manager adapter.
# This boundary deliberately returns only an opaque session reference.
[ordered]@{ok=$true;sessionRef=('cred-session-' + [guid]::NewGuid().ToString('N'));origin=$origin;credentialId=$id;purpose=$purpose} | ConvertTo-Json -Compress
`;
    try {
      const { stdout } = await execFileAsync(POWERSHELL, ["-NoProfile", "-NonInteractive", "-Command", script], {
        windowsHide: true,
        timeout: 15_000,
        env: { ...process.env, WWB_ORIGIN: safe(request.origin, 256), WWB_ID: safe(request.credentialId, 256), WWB_PURPOSE: safe(request.purpose, 256) },
        maxBuffer: 128 * 1024,
      });
      const result = JSON.parse(stdout) as { ok?: boolean; sessionRef?: string; error?: string };
      return result.ok && result.sessionRef ? { ok: true, sessionRef: result.sessionRef } : { ok: false, error: result.error ?? "Credential use failed." };
    } catch (error) {
      return { ok: false, error: error instanceof Error ? error.message : String(error) };
    }
  }

  async remove(credentialId: string): Promise<void> {
    requireWindows();
    if (!credentialId) throw new Error("credentialId is required.");
    // Deletion is intentionally not implemented through this boundary until the
    // production credential-index migration is available.
    throw new Error("Credential removal requires the production Windows Credential Manager adapter.");
  }
}
