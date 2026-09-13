import { execFile } from "node:child_process";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { promisify } from "node:util";
import type { CredentialRef, CredentialUseRequest, CredentialVault } from "../agent/credential-vault-contract";

const execFileAsync = promisify(execFile);

interface VaultRecord {
  origin: string;
  username?: string;
  protectedSecret: string;
}

/** Windows-only DPAPI-backed credential adapter with local persistence. */
export class WindowsCredentialVault implements CredentialVault {
  private readonly filePath: string;
  private readonly records = new Map<string, VaultRecord>();
  private loaded = false;

  constructor(filePath = `${process.env.LOCALAPPDATA ?? process.cwd()}\\WindowsWorkBrowser\\vault.json`) {
    this.filePath = filePath;
  }

  private async load(): Promise<void> {
    if (this.loaded) return;
    this.loaded = true;
    try {
      const raw = await readFile(this.filePath, "utf8");
      const parsed = JSON.parse(raw) as Record<string, VaultRecord>;
      for (const [id, record] of Object.entries(parsed)) {
        if (record && typeof record.origin === "string" && typeof record.protectedSecret === "string") {
          this.records.set(id, record);
        }
      }
    } catch (error) {
      const code = error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "";
      if (code !== "ENOENT") throw error;
    }
  }

  private async persist(): Promise<void> {
    await mkdir(dirname(this.filePath), { recursive: true });
    const body = Object.fromEntries(this.records.entries());
    await writeFile(this.filePath, `${JSON.stringify(body, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
  }

  async list(origin?: string): Promise<ReadonlyArray<CredentialRef>> {
    await this.load();
    const result: CredentialRef[] = [];
    for (const [id, record] of this.records) {
      if (origin && record.origin !== origin) continue;
      result.push({ id, origin: record.origin, ...(record.username ? { username: record.username } : {}) });
    }
    return result;
  }

  async save(id: string, origin: string, secret: string, username?: string): Promise<void> {
    if (process.platform !== "win32") throw new Error("WindowsCredentialVault requires Windows.");
    if (!id || !origin || !secret) throw new Error("Credential id, origin and secret are required.");
    await this.load();

    // Use the Windows DPAPI directly instead of PowerShell Security cmdlets so
    // the implementation is independent of module auto-loading on hosted runners.
    const script = [
      "$ErrorActionPreference='Stop'",
      "Add-Type -AssemblyName System.Security",
      "$bytes=[Text.Encoding]::UTF8.GetBytes($env:WWB_SECRET)",
      "$protected=[Security.Cryptography.ProtectedData]::Protect($bytes,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)",
      "[Convert]::ToBase64String($protected)",
    ].join(";");
    const { stdout } = await execFileAsync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script], {
      env: { ...process.env, WWB_SECRET: secret },
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    const protectedSecret = stdout.trim();
    if (!protectedSecret) throw new Error("DPAPI protection returned an empty payload.");
    this.records.set(id, { origin, ...(username ? { username } : {}), protectedSecret });
    await this.persist();
  }

  async use(request: CredentialUseRequest): Promise<{ ok: boolean; sessionRef?: string; error?: string }> {
    await this.load();
    const record = this.records.get(request.credentialId);
    if (!record) return { ok: false, error: "credential-not-found" };
    if (record.origin !== request.origin) return { ok: false, error: "origin-mismatch" };
    if (!request.purpose.trim()) return { ok: false, error: "purpose-required" };

    const sessionRef = `cred-session-${request.credentialId}-${Date.now().toString(36)}`;
    return { ok: true, sessionRef };
  }

  async remove(credentialId: string): Promise<void> {
    await this.load();
    this.records.delete(credentialId);
    await this.persist();
  }

  getProtectedBlobForNativeBridge(credentialId: string): string | undefined {
    return this.records.get(credentialId)?.protectedSecret;
  }
}
