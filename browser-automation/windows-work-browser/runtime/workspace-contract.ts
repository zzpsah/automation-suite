export interface Workspace {
  id: string;
  name: string;
  homepage?: string;
  allowedDomains: string[];
  allowedCapabilities: string[];
  credentialOrigins: string[];
  defaultPrinter?: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkspaceStore {
  list(): Promise<ReadonlyArray<Workspace>>;
  get(id: string): Promise<Workspace | undefined>;
  save(workspace: Workspace): Promise<void>;
  remove(id: string): Promise<void>;
}

export interface WorkspaceContext {
  workspace: Workspace;
  taskId?: string;
}
