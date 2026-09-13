import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { SharpImageService } from "./image-service";

test("image service transforms a fixture and respects maxBytes", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-image-"));
  try {
    const input = path.join(root, "input.svg");
    const output = path.join(root, "output.webp");
    await writeFile(input, '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400"><rect width="600" height="400" fill="white"/><rect x="40" y="40" width="520" height="320" fill="black"/></svg>');
    const result = await new SharpImageService().transform({
      input,
      output,
      crop: { x: 0, y: 0, width: 400, height: 400 },
      deskewDegrees: 2,
      resize: { width: 200, keepAspect: true },
      format: "webp",
      maxBytes: 100_000,
    });
    assert.equal(result.output, output);
    assert.ok(result.bytes > 0 && result.bytes <= 100_000);
    assert.equal((await readFile(output)).length, result.bytes);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
