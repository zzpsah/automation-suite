# Photo Prep Studio

A Windows/PyQt6 desktop tool for quickly preparing passport photographs and signatures.

## Main workflow

1. Open a photo.
2. Use **Select** to draw a rectangle around the required area.
3. In the right-side **Photo Preparation** panel choose a preset:
   - **Passport Photo — 35×45 mm (300 DPI)** → 413×531 px
   - **Signature** → 140×60 px
   - **Custom** → enter any width/height
4. Click **One Click: Crop + White Background**.
   - The selected region is used as the crop.
   - `rembg` removes the original background locally.
   - Transparency is flattened to white.
   - The result is resized to the configured pixel dimensions.
5. Set the maximum file size in KB and click **Export Prepared JPEG…**.

The output keeps the configured pixel dimensions and automatically chooses the highest JPEG quality that fits under the requested KB limit when possible.

## Other tools

Brush, pencil, eraser, line, rectangle, ellipse, copy/paste, undo/redo, crop, rotate, flip, auto-enhance, brightness/contrast/saturation/sharpness, zoom, PNG/JPEG save.

## Run from source

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

`rembg` may download its background-removal model on first use.

## Windows build

The repository GitHub Action builds a portable Windows application. Open the latest **Build Photo Prep Studio Windows** workflow under GitHub Actions and download the `PhotoPrepStudio-Windows` artifact.
