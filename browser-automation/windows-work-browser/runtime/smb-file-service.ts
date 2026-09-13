import { LocalFileService } from "./local-file-service";
import type { FileEntry } from "./capability-services";

/**
 * SMB on Windows is exposed through UNC paths. The service deliberately accepts
 * only an approved UNC root and delegates filesystem operations to the sandboxed
 * local adapter; credential negotiation stays with Windows/network drive policy.
 */
export class WindowsSmbFileService {
  private readonly root: string;
  private readonly delegate: LocalFileService;

  constructor(uncRoot: string) {
    if (process.platform !== "win32") throw new Error("SMB adapter requires Windows.");
    if (!/^\\\\[^\\]+\\[^\\]+/.test(uncRoot)) throw new Error("SMB root must be a UNC path.");
    this.root = uncRoot.replace(/[\\/]+$/, "");
    this.delegate = new LocalFileService({ root: this.root });
  }

  async list(relativePath = "."): Promise<ReadonlyArray<FileEntry>> {
    const entries = await this.delegate.list("local", relativePath);
    return entries.map((entry) => ({ ...entry, kind: "smb" as const, id: `smb:${entry.id}` }));
  }

  async read(entry: FileEntry): Promise<Uint8Array> {
    return this.delegate.read({ ...entry, kind: "local", id: entry.id.replace(/^smb:/, "") });
  }

  async write(relativePath: string, data: Uint8Array): Promise<void> { await this.delegate.write(relativePath, data); }
  async move(source: string, target: string): Promise<void> { await this.delegate.move(source, target); }
  async remove(relativePath: string): Promise<void> { await this.delegate.remove(relativePath); }

  get uncRoot(): string { return this.root; }
}
