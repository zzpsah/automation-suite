export type FileKind = "local" | "ftp" | "sftp" | "webdav" | "smb";

export interface FileEntry {
  id: string;
  kind: FileKind;
  name: string;
  path: string;
  size?: number;
  modifiedAt?: string;
}

export interface FileService {
  list(kind: FileKind, path: string): Promise<ReadonlyArray<FileEntry>>;
  read(entry: FileEntry): Promise<Uint8Array>;
  write(path: string, data: Uint8Array): Promise<void>;
  move(source: string, target: string): Promise<void>;
  remove(path: string): Promise<void>;
}

export interface PdfService {
  merge(inputs: string[], output: string): Promise<void>;
  split(input: string, pages: number[] | { from: number; to: number }, output: string): Promise<void>;
  ocr(input: string, output: string, language?: string): Promise<void>;
  exportPages(input: string, pages: number[], output: string): Promise<void>;
  print(input: string, printer?: string): Promise<void>;
}

export interface ImageTransform {
  input: string;
  output: string;
  crop?: { x: number; y: number; width: number; height: number };
  deskewDegrees?: number;
  resize?: { width?: number; height?: number; keepAspect?: boolean };
  removeBackground?: boolean;
  maxBytes?: number;
  format?: "png" | "jpeg" | "webp";
}

export interface ImageService {
  transform(request: ImageTransform): Promise<{ output: string; bytes: number }>; 
}

export interface CommunicationService {
  list(conversation?: string): Promise<ReadonlyArray<{ id: string; channel: string; sender?: string; text: string; receivedAt: string }>>;
  send(request: { channel: string; destination: string; text: string; attachmentPaths?: string[] }): Promise<{ messageId: string }>;
}

export interface WorkflowService {
  create(name: string, definition: unknown): Promise<{ id: string }>;
  run(id: string, input?: unknown): Promise<{ taskId: string }>;
  pause(taskId: string): Promise<void>;
  resume(taskId: string): Promise<void>;
  cancel(taskId: string): Promise<void>;
}
