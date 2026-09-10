import argparse
import json
import os
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
import winreg
from datetime import datetime
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageWin
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pystray
import uvicorn
import win32con
import win32gui
import win32print
import win32ui

APP_PORT = 8765
DISCOVERY_PORT = 8766
APP_NAME = "PhonePrinterHub"
DB_PATH = Path(os.getenv("LOCALAPPDATA", ".")) / APP_NAME / "jobs.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Phone Printer Hub", version="0.3.0")

PAPER_IDS = {"A4": 9, "Letter": 1, "Legal": 5, "A5": 11}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                printer TEXT NOT NULL,
                source TEXT,
                status TEXT NOT NULL,
                error TEXT,
                copies INTEGER NOT NULL,
                color INTEGER NOT NULL,
                duplex TEXT NOT NULL,
                orientation TEXT NOT NULL,
                paper_size TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def installed_printers():
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    return [item[2] for item in win32print.EnumPrinters(flags)]


def printer_status(printer_name):
    try:
        handle = win32print.OpenPrinter(printer_name)
        info = win32print.GetPrinter(handle, 2)
        win32print.ClosePrinter(handle)
        status = info.get("Status", 0)
        return {"name": printer_name, "status_code": status, "online": status == 0, "attributes": info.get("Attributes", 0)}
    except Exception as exc:
        return {"name": printer_name, "online": False, "error": str(exc)}


def local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def create_job(file_name, printer, source, copies, color, duplex, orientation, paper_size):
    job_id = uuid.uuid4().hex[:12]
    with db() as conn:
        conn.execute(
            "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, file_name, printer, source, "queued", None, copies, int(color), duplex, orientation, paper_size, now_iso(), now_iso()),
        )
    return job_id


def update_job(job_id, status, error=None):
    with db() as conn:
        conn.execute("UPDATE jobs SET status=?, error=?, updated_at=? WHERE id=?", (status, error, now_iso(), job_id))


def get_jobs(limit=100):
    with db() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


def get_job(job_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def render_pages(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        doc = fitz.open(path)
        try:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                yield Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        finally:
            doc.close()
    else:
        image = Image.open(path).convert("RGB")
        try:
            yield image.copy()
        finally:
            image.close()


def configure_devmode(printer_name, color, duplex, orientation, paper_size):
    handle = win32print.OpenPrinter(printer_name)
    try:
        info = win32print.GetPrinter(handle, 2)
        devmode = info["pDevMode"]
        devmode.Orientation = 2 if orientation == "Landscape" else 1
        devmode.Color = 2 if color else 1
        devmode.Duplex = {"Simplex": 1, "Long edge": 2, "Short edge": 3}.get(duplex, 1)
        devmode.PaperSize = PAPER_IDS.get(paper_size, 9)
        devmode.Fields |= 0x00000001 | 0x00000002 | 0x00000800 | 0x00001000
        return devmode
    finally:
        win32print.ClosePrinter(handle)


def print_document(path, printer_name, copies, color, duplex, orientation, paper_size):
    devmode = configure_devmode(printer_name, color, duplex, orientation, paper_size)
    hdc = win32gui.CreateDC("WINSPOOL", printer_name, None, devmode)
    dc = win32ui.CreateDCFromHandle(hdc)
    try:
        printable_w = dc.GetDeviceCaps(win32con.HORZRES)
        printable_h = dc.GetDeviceCaps(win32con.VERTRES)
        offset_x = dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
        offset_y = dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)
        for _ in range(max(1, min(copies, 99))):
            dc.StartDoc(Path(path).name)
            try:
                for page_image in render_pages(path):
                    image = page_image.convert("RGB") if color else page_image.convert("L").convert("RGB")
                    iw, ih = image.size
                    scale = min(printable_w / iw, printable_h / ih)
                    width = max(1, int(iw * scale))
                    height = max(1, int(ih * scale))
                    left = offset_x + max(0, (printable_w - width) // 2)
                    top = offset_y + max(0, (printable_h - height) // 2)
                    dc.StartPage()
                    try:
                        ImageWin.Dib(image).draw(dc.GetHandleOutput(), (left, top, left + width, top + height))
                    finally:
                        dc.EndPage()
            finally:
                dc.EndDoc()
    finally:
        dc.DeleteDC()


def process_job(job_id, path, options):
    try:
        update_job(job_id, "printing")
        print_document(path, options["printer"], options["copies"], options["color"], options["duplex"], options["orientation"], options["paper_size"])
        update_job(job_id, "completed")
    except Exception as exc:
        update_job(job_id, "failed", str(exc))
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def discovery_loop():
    beacon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    beacon.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", DISCOVERY_PORT))
    listener.settimeout(0.8)
    name = socket.gethostname()
    while True:
        payload = json.dumps({"service": "PHONE_PRINTER", "name": name, "port": APP_PORT}).encode()
        try:
            beacon.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
        except OSError:
            pass
        try:
            data, addr = listener.recvfrom(2048)
            if data.decode(errors="ignore").strip() == "DISCOVER_PHONE_PRINTER":
                listener.sendto(payload, addr)
        except socket.timeout:
            pass
        except OSError:
            pass
        time.sleep(1.2)


def startup_command():
    exe = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    if getattr(sys, "frozen", False):
        return f'"{exe}" --background'
    return f'"{sys.executable}" "{exe}" --background'


def install_startup():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, startup_command())
    winreg.CloseKey(key)


def remove_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass


def startup_installed():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def hide_console():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
    except Exception:
        pass


def make_tray_icon():
    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 20, 54, 46), outline="black", width=4)
    draw.rectangle((18, 8, 46, 28), outline="black", width=4)
    draw.rectangle((18, 40, 46, 56), outline="black", width=4)
    return image


def tray_loop():
    def open_ui(icon, item):
        webbrowser.open(f"http://127.0.0.1:{APP_PORT}")

    def quit_app(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Open Print Hub", open_ui, default=True),
        pystray.MenuItem("Exit", quit_app),
    )
    icon = pystray.Icon(APP_NAME, make_tray_icon(), "Phone Printer Hub", menu)
    icon.run()


@app.on_event("startup")
def startup():
    init_db()
    threading.Thread(target=discovery_loop, daemon=True).start()


WEB_PAGE = """
<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Phone Printer Hub</title><style>
body{font-family:system-ui;max-width:760px;margin:24px auto;padding:0 16px;background:#f5f5f5}.card{background:white;padding:18px;border-radius:14px;margin:12px 0;box-shadow:0 1px 5px #bbb}input,select,button{width:100%;padding:11px;margin:7px 0;box-sizing:border-box}button{font-weight:700}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:7px;border-bottom:1px solid #ddd;text-align:left}.ok{color:green}.bad{color:#b00020}
</style></head><body>
<h1>Phone Printer Hub</h1><div class='card'><form action='/print' method='post' enctype='multipart/form-data'>
<label>Printer</label><select id='printer' name='printer'></select><label>File</label><input type='file' name='file' accept='.pdf,image/*' required>
<label>Copies</label><input type='number' name='copies' value='1' min='1' max='99'><label>Color</label><select name='color'><option value='true'>Color</option><option value='false'>Black & White</option></select>
<label>Duplex</label><select name='duplex'><option>Simplex</option><option>Long edge</option><option>Short edge</option></select><label>Orientation</label><select name='orientation'><option>Portrait</option><option>Landscape</option></select>
<label>Paper size</label><select name='paper_size'><option>A4</option><option>Letter</option><option>Legal</option><option>A5</option></select><input type='hidden' name='source' value='Browser'><button type='submit'>PRINT</button></form></div>
<div class='card'><h2>Recent jobs</h2><table id='jobs'></table></div><script>
async function refresh(){let p=await fetch('/printers').then(r=>r.json());printer.innerHTML=p.printers.map(x=>`<option>${x}</option>`).join('');let j=await fetch('/jobs').then(r=>r.json());jobs.innerHTML='<tr><th>File</th><th>Printer</th><th>Status</th><th>Time</th></tr>'+j.jobs.slice(0,20).map(x=>`<tr><td>${x.file_name}</td><td>${x.printer}</td><td class='${x.status==='failed'?'bad':'ok'}'>${x.status}${x.error?' - '+x.error:''}</td><td>${x.created_at}</td></tr>`).join('')}refresh();setInterval(refresh,3000)
</script></body></html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    return WEB_PAGE


@app.get("/api")
def api_info():
    return {"status": "running", "name": socket.gethostname(), "ip": local_ip(), "port": APP_PORT}


@app.get("/printers")
def printers():
    names = installed_printers()
    return {"printers": names, "details": [printer_status(name) for name in names]}


@app.get("/jobs")
def jobs(limit: int = 100):
    return {"jobs": get_jobs(min(max(limit, 1), 500))}


@app.get("/jobs/{job_id}")
def job(job_id: str):
    item = get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    return item


@app.post("/print")
async def print_file(printer: str = Form(...), file: UploadFile = File(...), copies: int = Form(1), color: bool = Form(True), duplex: str = Form("Simplex"), orientation: str = Form("Portrait"), paper_size: str = Form("A4"), source: str = Form("Unknown device")):
    if printer not in installed_printers():
        raise HTTPException(status_code=400, detail="Selected printer is not installed on this PC")
    if copies < 1 or copies > 99:
        raise HTTPException(status_code=400, detail="Copies must be between 1 and 99")
    if duplex not in {"Simplex", "Long edge", "Short edge"} or orientation not in {"Portrait", "Landscape"} or paper_size not in PAPER_IDS:
        raise HTTPException(status_code=400, detail="Invalid print option")
    suffix = Path(file.filename or "document.pdf").suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
        raise HTTPException(status_code=400, detail="Only PDF and image files are supported")
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(await file.read())
    temp.close()
    job_id = create_job(file.filename or "document", printer, source, copies, color, duplex, orientation, paper_size)
    options = {"printer": printer, "copies": copies, "color": color, "duplex": duplex, "orientation": orientation, "paper_size": paper_size}
    threading.Thread(target=process_job, args=(job_id, temp.name, options), daemon=True).start()
    return JSONResponse({"success": True, "job_id": job_id, "status": "queued"})


def server_running():
    try:
        with socket.create_connection(("127.0.0.1", APP_PORT), timeout=0.4):
            return True
    except OSError:
        return False


def print_status():
    print(json.dumps({"server_running": server_running(), "url": f"http://{local_ip()}:{APP_PORT}", "startup": startup_installed()}, indent=2))


def parse_args():
    p = argparse.ArgumentParser(description="Phone Printer Hub")
    p.add_argument("--background", action="store_true", help="Run server minimized to tray")
    p.add_argument("--show", action="store_true", help="Open local Print Hub in browser")
    p.add_argument("--status", action="store_true", help="Show server/startup status")
    p.add_argument("--install-startup", action="store_true", help="Start Print Hub in background when this user signs in")
    p.add_argument("--remove-startup", action="store_true", help="Remove automatic startup")
    return p.parse_args()


def main():
    args = parse_args()
    if args.show:
        webbrowser.open(f"http://127.0.0.1:{APP_PORT}")
        return
    if args.status:
        print_status(); return
    if args.install_startup:
        install_startup(); print("Startup enabled."); return
    if args.remove_startup:
        remove_startup(); print("Startup disabled."); return

    if args.background:
        hide_console()
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level="warning"), daemon=True).start()
    if not args.background:
        print(f"Phone Printer Hub running at http://{local_ip()}:{APP_PORT}")
    tray_loop()


if __name__ == "__main__":
    main()
