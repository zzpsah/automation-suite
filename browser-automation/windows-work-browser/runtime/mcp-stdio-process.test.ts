import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { join } from "node:path";

function runRequest(command: string, args: string[], request: object): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ["pipe", "pipe", "pipe"] });
    let buffer = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`MCP stdio timeout; stderr=${stderr}`));
    }, 5000);
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk: string) => { stderr += chunk; });
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      buffer += chunk;
      const newline = buffer.indexOf("\n");
      if (newline < 0) return;
      clearTimeout(timer);
      try {
        resolve(JSON.parse(buffer.slice(0, newline)) as Record<string, unknown>);
      } catch (error) {
        reject(error);
      } finally {
        child.kill();
      }
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.stdin.end(`${JSON.stringify(request)}\n`);
  });
}

test("MCP stdio works as an external child process", async () => {
  const serverPath = join(__dirname, "mcp-stdio-server.js");
  const result = await runRequest(process.execPath, [serverPath], {
    jsonrpc: "2.0",
    id: 1,
    method: "tools/list",
  });
  const tools = (result.result as { tools: Array<{ name: string }> }).tools;
  assert.ok(tools.some((tool) => tool.name === "browser.navigate"));
});
