export interface FileEntry {
  uri: string;
  name: string;
  kind: "file" | "directory";
  size?: number;
  modifiedAt?: string;
}

export type RemoteProtocol = "local" | "ftp" | "sftp" | "webdav" | "smb";

export interface FileWorkspace {
  id: string;
  protocol: RemoteProtocol;
  root: string;
  label: string;
}

export interface FileBrowser {
  list(workspace: FileWorkspace, path?: string): Promise<ReadonlyArray<FileEntry>>;
  copy(sourceUri: string, destinationUri: string): Promise<void>;
  move(sourceUri: string, destinationUri: string): Promise<void>;
  remove(uri: string): Promise<void>;
  createDirectory(uri: string): Promise<void>;
}

export interface PdfOperation {
  operation: "merge" | "split" | "rotate" | "extract-pages" | "compress" | "ocr" | "print" | "save-as";
  inputRefs: string[];
  outputRef?: string;
  options?: Record<string, unknown>;
}

export interface PdfService {
  execute(operation: PdfOperation): Promise<{ ok: boolean; outputRef?: string; detail?: string }>;
}

export interface ImageOperation {
  operation: "crop" | "deskew" | "resize" | "compress" | "remove-background" | "convert";
  inputRef: string;
  outputRef?: string;
  options?: { width?: number; height?: number; format?: "png" | "jpg" | "webp"; maxBytes?: number };
}

export interface ImageService {
  execute(operation: ImageOperation): Promise<{ ok: boolean; outputRef?: string; detail?: string }>;
}

export interface CommunicationProvider {
  id: string;
  listInbox(): Promise<ReadonlyArray<{ id: string; sender: string; receivedAt: string; hasAttachment: boolean }>>;
  send(request: { recipientRef: string; body: string; attachmentRefs?: string[] }): Promise<{ ok: boolean; messageRef?: string }>;
}
