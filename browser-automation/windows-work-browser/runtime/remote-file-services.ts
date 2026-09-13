import { Client as FtpClient } from "basic-ftp";
import SftpClient from "ssh2-sftp-client";
import { createClient as createWebDavClient } from "webdav";
import { promises as fs } from "node:fs";
import * as path from "node:path";
import type { FileEntry } from "./capability-services";

export interface FtpConnection {
  host: string;
  user: string;
  password: string;
  port?: number;
  secure?: boolean;
}

export class FtpFileService {
  async list(connection: FtpConnection, remotePath: string): Promise<ReadonlyArray<FileEntry>> {
    const client = new FtpClient(15_000);
    try {
      await client.access({ host: connection.host, user: connection.user, password: connection.password, port: connection.port, secure: connection.secure ?? false });
      const entries = await client.list(remotePath);
      return entries.map((entry) => ({
        id: `${connection.host}:${remotePath}/${entry.name}`,
        kind: "ftp" as const,
        name: entry.name,
        path: `${remotePath.replace(/\/$/, "")}/${entry.name}`,
        ...(entry.size !== undefined ? { size: entry.size } : {}),
        ...(entry.modifiedAt ? { modifiedAt: entry.modifiedAt.toISOString() } : {}),
      }));
    } finally { client.close(); }
  }

  async download(connection: FtpConnection, remotePath: string, localPath: string): Promise<void> {
    const client = new FtpClient(15_000);
    try {
      await fs.mkdir(path.dirname(localPath), { recursive: true });
      await client.access({ host: connection.host, user: connection.user, password: connection.password, port: connection.port, secure: connection.secure ?? false });
      await client.downloadTo(localPath, remotePath);
    } finally { client.close(); }
  }

  async upload(connection: FtpConnection, localPath: string, remotePath: string): Promise<void> {
    const client = new FtpClient(15_000);
    try {
      await client.access({ host: connection.host, user: connection.user, password: connection.password, port: connection.port, secure: connection.secure ?? false });
      await client.uploadFrom(localPath, remotePath);
    } finally { client.close(); }
  }

  async move(connection: FtpConnection, source: string, target: string): Promise<void> {
    const client = new FtpClient(15_000);
    try {
      await client.access({ host: connection.host, user: connection.user, password: connection.password, port: connection.port, secure: connection.secure ?? false });
      await client.rename(source, target);
    } finally { client.close(); }
  }

  async remove(connection: FtpConnection, remotePath: string): Promise<void> {
    const client = new FtpClient(15_000);
    try {
      await client.access({ host: connection.host, user: connection.user, password: connection.password, port: connection.port, secure: connection.secure ?? false });
      await client.remove(remotePath);
    } finally { client.close(); }
  }
}

export interface SftpConnection {
  host: string;
  username: string;
  port?: number;
  password?: string;
  privateKey?: string;
}

export class SftpFileService {
  async list(connection: SftpConnection, remotePath: string): Promise<ReadonlyArray<FileEntry>> {
    const client = new SftpClient();
    try {
      await client.connect(connection);
      const entries = await client.list(remotePath);
      return entries.map((entry) => ({
        id: `${connection.host}:${remotePath}/${entry.name}`,
        kind: "sftp" as const,
        name: entry.name,
        path: `${remotePath.replace(/\/$/, "")}/${entry.name}`,
        ...(entry.size !== undefined ? { size: entry.size } : {}),
        ...(entry.modifyTime ? { modifiedAt: new Date(entry.modifyTime).toISOString() } : {}),
      }));
    } finally { await client.end().catch(() => undefined); }
  }

  async download(connection: SftpConnection, remotePath: string, localPath: string): Promise<void> {
    const client = new SftpClient();
    try { await fs.mkdir(path.dirname(localPath), { recursive: true }); await client.connect(connection); await client.fastGet(remotePath, localPath); }
    finally { await client.end().catch(() => undefined); }
  }

  async upload(connection: SftpConnection, localPath: string, remotePath: string): Promise<void> {
    const client = new SftpClient();
    try { await client.connect(connection); await client.fastPut(localPath, remotePath); }
    finally { await client.end().catch(() => undefined); }
  }

  async move(connection: SftpConnection, source: string, target: string): Promise<void> {
    const client = new SftpClient();
    try { await client.connect(connection); await client.rename(source, target); }
    finally { await client.end().catch(() => undefined); }
  }

  async remove(connection: SftpConnection, remotePath: string): Promise<void> {
    const client = new SftpClient();
    try { await client.connect(connection); await client.delete(remotePath); }
    finally { await client.end().catch(() => undefined); }
  }
}

export interface WebDavConnection {
  url: string;
  username?: string;
  password?: string;
}

export class WebDavFileService {
  private client(connection: WebDavConnection) {
    return createWebDavClient(connection.url, connection.username ? { username: connection.username, password: connection.password ?? "" } : undefined);
  }

  async list(connection: WebDavConnection, remotePath: string): Promise<ReadonlyArray<FileEntry>> {
    const client = this.client(connection);
    const entries = await client.getDirectoryContents(remotePath);
    return entries.map((entry) => ({
      id: `${connection.url}:${entry.filename}`,
      kind: "webdav" as const,
      name: path.basename(entry.filename),
      path: entry.filename,
      ...(typeof entry.size === "number" ? { size: entry.size } : {}),
      ...(entry.lastmod ? { modifiedAt: entry.lastmod } : {}),
    }));
  }

  async download(connection: WebDavConnection, remotePath: string, localPath: string): Promise<void> {
    const client = this.client(connection);
    const data = await client.getFileContents(remotePath);
    await fs.mkdir(path.dirname(localPath), { recursive: true });
    await fs.writeFile(localPath, Buffer.isBuffer(data) ? data : Buffer.from(data as ArrayBuffer));
  }

  async upload(connection: WebDavConnection, localPath: string, remotePath: string): Promise<void> {
    const client = this.client(connection);
    await client.putFileContents(remotePath, await fs.readFile(localPath), { overwrite: true });
  }

  async move(connection: WebDavConnection, source: string, target: string): Promise<void> {
    await this.client(connection).moveFile(source, target);
  }

  async remove(connection: WebDavConnection, remotePath: string): Promise<void> {
    await this.client(connection).deleteFile(remotePath);
  }
}
