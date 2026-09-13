import { promises as fs } from "node:fs";
import { PDFDocument } from "@cantoo/pdf-lib";
import type { PdfService } from "./capability-services";

function validatePages(pages: number[]): void {
  if (pages.some((page) => !Number.isInteger(page) || page < 1)) throw new Error("PDF pages must be positive integers.");
}

async function load(input: string): Promise<PDFDocument> {
  return PDFDocument.load(await fs.readFile(input));
}

export class PdfLibService implements PdfService {
  async merge(inputs: string[], output: string): Promise<void> {
    if (inputs.length < 2) throw new Error("Merge requires at least two PDFs.");
    const out = await PDFDocument.create();
    for (const input of inputs) {
      const source = await load(input);
      const pages = await out.copyPages(source, source.getPageIndices());
      pages.forEach((page) => out.addPage(page));
    }
    await fs.writeFile(output, await out.save());
  }

  async split(input: string, pages: number[] | { from: number; to: number }, output: string): Promise<void> {
    const source = await load(input);
    const total = source.getPageCount();
    const selected = Array.isArray(pages)
      ? pages
      : Array.from({ length: pages.to - pages.from + 1 }, (_, i) => pages.from + i);
    validatePages(selected);
    if (selected.some((page) => page > total)) throw new Error("Requested PDF page is out of range.");
    const out = await PDFDocument.create();
    const copied = await out.copyPages(source, selected.map((page) => page - 1));
    copied.forEach((page) => out.addPage(page));
    await fs.writeFile(output, await out.save());
  }

  async ocr(_input: string, _output: string, _language = "eng"): Promise<void> {
    throw new Error("OCR requires a licensed/configured OCR engine; PDF text extraction is available separately.");
  }

  async exportPages(input: string, pages: number[], output: string): Promise<void> {
    await this.split(input, pages, output);
  }

  async print(_input: string, _printer?: string): Promise<void> {
    throw new Error("PDF print requires the bounded Windows print adapter.");
  }
}
