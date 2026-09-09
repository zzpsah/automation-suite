# PyPaint AI

An MS Paint clone built with **PyQt6**, featuring local AI background removal
(`rembg`) and an integrated **Google Gemini** (`gemini-2.5-flash`) chat side panel
that can analyze your canvas.

## Features
- Tool ribbon: Brush, Pencil, Eraser, Line, Rectangle, Ellipse, Select, Crop
- Primary/secondary color swatches + stroke width
- Undo (`Ctrl+Z`) / Redo (`Ctrl+Y`) history buffer
- Clipboard paste (`Ctrl+V`) with a movable floating selection
- Open/Save PNG, JPG, BMP
- One-click **Remove Background** (local `rembg` / U2-Net, no internet required)
- Crop, Rotate 90° CW/CCW, Flip H/V
- Adjustments dialog: Brightness, Contrast, Saturation, Sharpness (live preview)
- Auto-Enhance preset
- Dockable Gemini AI panel with chat history and a "send canvas with message" toggle

## 1. Install (Windows)

Open **PowerShell** or **Command Prompt**:

```powershell
# 1. Get Python 3.11+ if you don't have it: https://www.python.org/downloads/
python --version

# 2. Clone this repository, then enter this project folder
cd path\to\automation-suite\paint-gemini-app

# 3. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

> `rembg` will download its U2-Net model (~170 MB) automatically the first time
> you click "Remove Background". This requires an internet connection once;
> after that it's cached locally and works offline.

## 2. Set your Gemini API key (optional but needed for the AI panel)

Get a key from https://aistudio.google.com/apikey, then either:

**Option A — environment variable (persists across runs):**
```powershell
setx GEMINI_API_KEY "your-api-key-here"
# close and reopen your terminal for it to take effect
```

**Option B — paste it directly into the "API Key" field in the app's AI panel**
(not persisted between runs).

## 3. Run

```powershell
venv\Scripts\activate
python main.py
```

## Keyboard shortcuts

| Action              | Shortcut       |
|---------------------|----------------|
| Brush / Pencil / Eraser | B / P / E |
| Line / Rect / Ellipse   | L / R / O |
| Select / Crop           | S / C     |
| Undo / Redo              | Ctrl+Z / Ctrl+Y |
| Cut / Copy / Paste        | Ctrl+X / Ctrl+C / Ctrl+V |
| Delete selection          | Del |
| Crop to selection         | Ctrl+Shift+X |
| Adjustments dialog        | Ctrl+M |
| Auto-Enhance               | Ctrl+E |
| Zoom In / Out / Reset     | Ctrl+= / Ctrl+- / Ctrl+0 |
| New / Open / Save / Save As | Ctrl+N / Ctrl+O / Ctrl+S / Ctrl+Shift+S |

## Project layout

```text
paint-gemini-app/
├── main.py
├── canvas.py
├── bg_remover.py
├── gemini_panel.py
├── adjustments_dialog.py
├── requirements.txt
└── README.md
```

## Building a standalone .exe (optional)

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name PyPaintAI main.py
```

The executable will be in `dist\PyPaintAI.exe`. `rembg`'s ONNX model files are downloaded at runtime, so first use of background removal still needs internet access.

## Repository location

This project is maintained at:

```text
automation-suite/paint-gemini-app/
```

Repository: `zzpsah/automation-suite`
