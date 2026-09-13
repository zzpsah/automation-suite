declare module "ssh2-sftp-client" {
  interface ConnectOptions {
    host: string;
    username: string;
    port?: number;
    password?: string;
    privateKey?: string;
  }

  interface FileEntry {
    name: string;
    size?: number;
    modifyTime?: number;
    type?: string;
  }

  export default class SftpClient {
    connect(options: ConnectOptions): Promise<void>;
    list(remotePath: string): Promise<FileEntry[]>;
    fastGet(remotePath: string, localPath: string): Promise<void>;
    fastPut(localPath: string, remotePath: string): Promise<void>;
    rename(oldPath: string, newPath: string): Promise<void>;
    delete(remotePath: string): Promise<void>;
    end(): Promise<void>;
  }
}
