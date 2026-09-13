import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { PDFDocument } from "@cantoo/pdf-lib";
import { PdfLibService } from "./pdf-service";
import { SharpImageService } from "./image-service";

async function makePdf(file: string, pages: number): Promise<void> {
  const doc = await PDFDocument.create();
  for (let i = 0; i < pages; i += 1) doc.addPage([200, 200]);
  await writeFile(file, await doc.save());
}

test("PDF service merges and exports selected pages", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-pdf-"));
  try {
    const one = path.join(root, "one.pdf");
    const two = path.join(root, "two.pdf");
    const merged = path.join(root, "merged.pdf");
    const split = path.join(root, "split.pdf");
    await makePdf(one, 1);
    await makePdf(two, 2);
    const service = new PdfLibService();
    await service.merge([one, two], merged);
    const mergedDoc = await PDFDocument.load(await readFile(merged));
    assert.equal(mergedDoc.getPageCount(), 3);
    await service.exportPages(merged, [1, 3], split);
    const splitDoc = await PDFDocument.load(await readFile(split));
    assert.equal(splitDoc.getPageCount(), 2);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("image service crops, resizes and converts", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-image-"));
  try {
    const input = path.join(root, "in.svg");
    const output = path.join(root, "out.png");
    await writeFile(input, `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80"><rect width="100" height="80" fill="white"/></svg>`);
    const result = await new SharpImageService().transform({
      input,
      output,
      crop: { x: 0, y: 0, width: 80, height: 60 },
      resize: { width: 40, keepAspect: true },
      format: "png",
    });
    assert.equal(result.output, output);
    assert.ok(result.bytes > 0);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
