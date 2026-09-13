import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { createHash } from "node:crypto";
import { VerifiedUpdateManager } from "./update-manager";

function digest(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

test("update manager verifies, backs up and applies an artifact", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-update-"));
  try {
    const current = path.join(root, "app.bin");
    const next = path.join(root, "next.bin");
    await writeFile(current, "old");
    await writeFile(next, "new");
    const result = await new VerifiedUpdateManager().apply(current, { version: "1.1.0", artifactPath: next, sha256: digest("new") });
    assert.equal(await readFile(current, "utf8"), "new");
    assert.equal(await readFile(result.backupPath, "utf8"), "old");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("update manager rejects a bad digest without replacing current artifact", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-update-bad-"));
  try {
    const current = path.join(root, "app.bin");
    const next = path.join(root, "next.bin");
    await writeFile(current, "old");
    await writeFile(next, "new");
    await assert.rejects(() => new VerifiedUpdateManager().apply(current, { version: "1.1.0", artifactPath: next, sha256: digest("wrong") }));
    assert.equal(await readFile(current, "utf8"), "old");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
