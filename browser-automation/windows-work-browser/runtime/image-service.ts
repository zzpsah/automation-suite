import { promises as fs } from "node:fs";
import sharp from "sharp";
import type { ImageService, ImageTransform } from "./capability-services";

export class SharpImageService implements ImageService {
  async transform(request: ImageTransform): Promise<{ output: string; bytes: number }> {
    const input = sharp(request.input, { failOn: "warning" });
    let image = input;

    if (request.crop) {
      const { x, y, width, height } = request.crop;
      if (![x, y, width, height].every(Number.isInteger) || x < 0 || y < 0 || width <= 0 || height <= 0) {
        throw new Error("Invalid crop rectangle.");
      }
      image = image.extract({ left: x, top: y, width, height });
    }

    if (request.deskewDegrees !== undefined) {
      if (!Number.isFinite(request.deskewDegrees) || Math.abs(request.deskewDegrees) > 45) throw new Error("Deskew angle is outside the supported range.");
      image = image.rotate(request.deskewDegrees, { background: "white" });
    }

    if (request.resize) {
      const width = request.resize.width;
      const height = request.resize.height;
      if (width !== undefined && (!Number.isInteger(width) || width <= 0)) throw new Error("Invalid resize width.");
      if (height !== undefined && (!Number.isInteger(height) || height <= 0)) throw new Error("Invalid resize height.");
      image = image.resize({ width, height, fit: request.resize.keepAspect === false ? "fill" : "inside", withoutEnlargement: true });
    }

    if (request.removeBackground) {
      throw new Error("Background removal requires a dedicated segmentation model and is not silently approximated.");
    }

    switch (request.format) {
      case "png": image = image.png(); break;
      case "webp": image = image.webp({ quality: 88 }); break;
      case "jpeg": image = image.jpeg({ quality: 88, mozjpeg: true }); break;
      default: break;
    }

    let buffer = await image.toBuffer();
    if (request.maxBytes && buffer.length > request.maxBytes) {
      if (!request.format || request.format === "png") throw new Error("Target byte size requires JPEG or WebP output for deterministic compression.");
      const quality = request.format === "jpeg" ? 88 : 85;
      let q = quality;
      while (buffer.length > request.maxBytes && q >= 25) {
        const candidate = request.format === "jpeg"
          ? await sharp(buffer).jpeg({ quality: q, mozjpeg: true }).toBuffer()
          : await sharp(buffer).webp({ quality: q }).toBuffer();
        buffer = candidate;
        q -= 5;
      }
      if (buffer.length > request.maxBytes) throw new Error(`Unable to satisfy maxBytes=${request.maxBytes}.`);
    }

    await fs.writeFile(request.output, buffer);
    return { output: request.output, bytes: buffer.length };
  }
}
