import { promises as fs } from "node:fs";
import * as path from "node:path";
import { createHash } from "node:crypto";

export interface UpdateManifest {
  version: string;
  artifactPath: string;
  sha256: string;
}

export interface UpdateResult {
  version: string;
  artifactSha256: string;
  backupPath: string;
}

async function sha256(file: string): Promise<string> {
  const data = await fs.readFile(file);
  return createHash("sha256").update(data).digest("hex");
}

/** Local package updater with verify-before-replace and rollback backup semantics. */
export class VerifiedUpdateManager {
  async apply(currentPath: string, manifest: UpdateManifest): Promise<UpdateResult> {
    const expected = manifest.sha256.toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(expected)) throw new Error("Update manifest requires a valid SHA-256.");
    const actual = await sha256(manifest.artifactPath);
    if (actual !== expected) throw new Error(`Update SHA-256 mismatch: expected ${expected}, got ${actual}`);

    const backupPath = `${currentPath}.rollback-${Date.now()}`;
    await fs.copyFile(currentPath, backupPath);
    const staged = `${currentPath}.staged-${Date.now()}`;
    try {
      await fs.copyFile(manifest.artifactPath, staged);
      const stagedHash = await sha256(staged);
      if (stagedHash !== expected) throw new Error("Staged update hash changed before activation.");
      await fs.rename(staged, currentPath);
      return { version: manifest.version, artifactSha256: expected, backupPath };
    } catch (error) {
      await fs.rm(staged, { force: true }).catch(() => undefined);
      await fs.copyFile(backupPath, currentPath).catch(() => undefined);
      throw error;
    }
  }

  async rollback(currentPath: string, backupPath: string): Promise<void> {
    await fs.access(backupPath);
    const rollbackPath = `${currentPath}.rollback-verify-${Date.now()}`;
    await fs.copyFile(backupPath, rollbackPath);
    await fs.rename(rollbackPath, currentPath);
  }
}
