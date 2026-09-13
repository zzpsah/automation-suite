import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { PDFDocument } from "@cantoo/pdf-lib";
import { PdfLibService } from "./pdf-service";

test("PDF service merges, splits and refuses unconfigured OCR", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-pdf-"));
  try {
    const a = path.join(root, "a.pdf");
    const b = path.join(root, "b.pdf");
    const merged = path.join(root, "merged.pdf");
    const split = path.join(root, "split.pdf");
    for (const target of [a, b]) {
      const doc = await PDFDocument.create();
      doc.addPage([300, 400]);
      await writeFile(target, await doc.save());
    }
    const service = new PdfLibService();
    await service.merge([a, b], merged);
    const mergedDoc = await PDFDocument.load(await readFile(merged));
    assert.equal(mergedDoc.getPageCount(), 2);
    await service.split(merged, { from: 2, to: 2 }, split);
    const splitDoc = await PDFDocument.load(await readFile(split));
    assert.equal(splitDoc.getPageCount(), 1);
    await assert.rejects(() => service.ocr(merged, path.join(root, "ocr.txt")), /OCR requires/i);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
