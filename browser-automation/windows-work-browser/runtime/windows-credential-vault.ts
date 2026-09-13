import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { CredentialRef, CredentialUseRequest, CredentialVault } from "../agent/credential-vault-contract";

const execFileAsync = promisify(execFile);

interface VaultRecord {
  origin: string;
  username?: string;
  protectedSecret: string;
}

/** Windows-only DPAPI-backed credential adapter. */
export class WindowsCredentialVault implements CredentialVault {
  private readonly records = new Map<string, VaultRecord>();

  async list(origin?: string): Promise<ReadonlyArray<CredentialRef>> {
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

    const script = [
      "$ErrorActionPreference='Stop'",
      "$s=ConvertTo-SecureString $env:WWB_SECRET -AsPlainText -Force",
      "$s | ConvertFrom-SecureString",
    ].join(";");
    const { stdout } = await execFileAsync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script], {
      env: { ...process.env, WWB_SECRET: secret },
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    const protectedSecret = stdout.trim();
    if (!protectedSecret) throw new Error("DPAPI protection returned an empty payload.");
    this.records.set(id, { origin, ...(username ? { username } : {}), protectedSecret });
  }

  async use(request: CredentialUseRequest): Promise<{ ok: boolean; sessionRef?: string; error?: string }> {
    const record = this.records.get(request.credentialId);
    if (!record) return { ok: false, error: "credential-not-found" };
    if (record.origin !== request.origin) return { ok: false, error: "origin-mismatch" };
    if (!request.purpose.trim()) return { ok: false, error: "purpose-required" };

    // The plaintext is intentionally never returned to the model. A native bridge
    // can consume this opaque protected blob inside the OS boundary.
    const sessionRef = `cred-session-${request.credentialId}-${Date.now().toString(36)}`;
    return { ok: true, sessionRef };
  }

  async remove(credentialId: string): Promise<void> {
    this.records.delete(credentialId);
  }

  getProtectedBlobForNativeBridge(credentialId: string): string | undefined {
    return this.records.get(credentialId)?.protectedSecret;
  }
}
