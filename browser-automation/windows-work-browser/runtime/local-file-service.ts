import { promises as fs } from "node:fs";
import * as path from "node:path";
import type { FileEntry, FileKind, FileService } from "./capability-services";

export interface LocalFileServiceOptions {
  root: string;
}

/** Workspace-scoped local file adapter. Remote transports intentionally stay separate. */
export class LocalFileService implements FileService {
  private readonly root: string;

  constructor(options: LocalFileServiceOptions) {
    this.root = path.resolve(options.root);
  }

  private resolve(relativePath: string): string {
    const candidate = path.resolve(this.root, relativePath);
    const rel = path.relative(this.root, candidate);
    if (rel === "" || (!rel.startsWith(".." + path.sep) && rel !== ".." && !path.isAbsolute(rel))) return candidate;
    throw new Error("Path escapes workspace root.");
  }

  async list(kind: FileKind, relativePath: string): Promise<ReadonlyArray<FileEntry>> {
    if (kind !== "local") throw new Error(`Remote file transport '${kind}' is not configured.`);
    const directory = this.resolve(relativePath);
    const entries = await fs.readdir(directory, { withFileTypes: true });
    return Promise.all(entries.map(async (entry) => {
      const full = path.join(directory, entry.name);
      const stat = await fs.stat(full);
      return {
        id: full,
        kind: "local" as const,
        name: entry.name,
        path: path.relative(this.root, full),
        ...(entry.isFile() ? { size: stat.size } : {}),
        modifiedAt: stat.mtime.toISOString(),
      };
    }));
  }

  async read(entry: FileEntry): Promise<Uint8Array> {
    if (entry.kind !== "local") throw new Error(`Unsupported file kind: ${entry.kind}`);
    return fs.readFile(this.resolve(entry.path));
  }

  async write(relativePath: string, data: Uint8Array): Promise<void> {
    const target = this.resolve(relativePath);
    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, data);
  }

  async move(source: string, target: string): Promise<void> {
    const sourcePath = this.resolve(source);
    const targetPath = this.resolve(target);
    await fs.mkdir(path.dirname(targetPath), { recursive: true });
    await fs.rename(sourcePath, targetPath);
  }

  async remove(relativePath: string): Promise<void> {
    await fs.rm(this.resolve(relativePath), { force: false });
  }
}
