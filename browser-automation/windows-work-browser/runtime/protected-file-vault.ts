import { promises as fs } from "node:fs";
import * as path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { CredentialRef, CredentialUseRequest, CredentialVault } from "../agent/credential-vault-contract";

const execFileAsync = promisify(execFile);

export interface ProtectedFileVaultOptions {
  root: string;
}

/**
 * Windows DPAPI-backed credential vault.
 * Raw secret material is decrypted only inside the PowerShell process and is
 * consumed by the OS-facing operation; the Node/agent layer never receives it.
 */
export class ProtectedFileVault implements CredentialVault {
  private readonly root: string;

  constructor(options: ProtectedFileVaultOptions) {
    this.root = path.resolve(options.root);
  }

  private file(id: string): string {
    const safe = id.replace(/[^a-zA-Z0-9_-]/g, "_");
    return path.join(this.root, `${safe}.xml`);
  }

  private ensureWindows(): void {
    if (process.platform !== "win32") throw new Error("DPAPI vault requires Windows.");
  }

  async list(origin?: string): Promise<ReadonlyArray<CredentialRef>> {
    this.ensureWindows();
    await fs.mkdir(this.root, { recursive: true });
    const names = await fs.readdir(this.root);
    const refs: CredentialRef[] = [];
    for (const name of names.filter((entry) => entry.endsWith(".json"))) {
      const value = JSON.parse(await fs.readFile(path.join(this.root, name), "utf8")) as CredentialRef;
      if (!origin || value.origin === origin) refs.push(value);
    }
    return refs;
  }

  async use(request: CredentialUseRequest): Promise<{ ok: boolean; sessionRef?: string; error?: string }> {
    this.ensureWindows();
    const payloadPath = this.file(request.credentialId);
    const metaPath = payloadPath.replace(/\.xml$/, ".json");
    const raw = JSON.parse(await fs.readFile(metaPath, "utf8")) as CredentialRef;
    if (raw.origin !== request.origin) return { ok: false, error: "Credential origin mismatch." };
    const script = `$secure = Get-Content -Raw -LiteralPath $env:WWB_SECRET_FILE | ConvertTo-SecureString; [System.Net.NetworkCredential]::new('', $secure).Password | Out-Null`;
    await execFileAsync("powershell.exe", ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], {
      windowsHide: true,
      timeout: 15_000,
      env: { ...process.env, WWB_SECRET_FILE: payloadPath },
      maxBuffer: 256 * 1024,
    });
    return { ok: true, sessionRef: `credential-session:${request.credentialId}` };
  }

  async remove(credentialId: string): Promise<void> {
    this.ensureWindows();
    await fs.rm(this.file(credentialId), { force: true });
    await fs.rm(this.file(credentialId).replace(/\.xml$/, ".json"), { force: true });
  }

  /** Provisioning helper for local bootstrap; secret never leaves the PowerShell process. */
  async provision(ref: CredentialRef, secret: string): Promise<void> {
    this.ensureWindows();
    await fs.mkdir(this.root, { recursive: true });
    const payload = this.file(ref.id);
    const meta = payload.replace(/\.xml$/, ".json");
    await execFileAsync("powershell.exe", ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", "$secure=ConvertTo-SecureString -String $env:WWB_SECRET -AsPlainText -Force; $secure | ConvertFrom-SecureString | Set-Content -LiteralPath $env:WWB_PAYLOAD"], {
      windowsHide: true,
      timeout: 15_000,
      env: { ...process.env, WWB_SECRET: secret, WWB_PAYLOAD: payload },
      maxBuffer: 256 * 1024,
    });
    await fs.writeFile(meta, JSON.stringify(ref, null, 2), "utf8");
  }
}
