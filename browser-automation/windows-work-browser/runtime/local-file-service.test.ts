import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { LocalFileService } from "./local-file-service";

test("local file service supports workspace lifecycle and blocks traversal", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-files-"));
  try {
    const service = new LocalFileService({ root });
    await service.write("nested/data.csv", Buffer.from("id,name\n1,Alpha\n"));
    const listed = await service.list("local", "nested");
    assert.equal(listed.length, 1);
    assert.equal(listed[0]?.name, "data.csv");
    const data = await service.read(listed[0]!);
    assert.equal(Buffer.from(data).toString(), "id,name\n1,Alpha\n");
    await service.move("nested/data.csv", "renamed.csv");
    assert.equal((await readFile(path.join(root, "renamed.csv"))).toString(), "id,name\n1,Alpha\n");
    await service.remove("renamed.csv");
    await assert.rejects(() => service.write("../escape.txt", Buffer.from("nope")), /escapes workspace/i);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
