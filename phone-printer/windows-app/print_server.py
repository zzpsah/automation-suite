import os
import tempfile
import socket
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import win32print
import win32api

APP_PORT = 8765
app = FastAPI(title="Phone USB Printer Bridge", version="0.1.0")


def installed_printers():
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    return [item[2] for item in win32print.EnumPrinters(flags)]


def local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


@app.get("/")
def root():
    return {
        "status": "running",
        "name": "Phone USB Printer Bridge",
        "ip": local_ip(),
        "port": APP_PORT,
    }


@app.get("/printers")
def printers():
    return {"printers": installed_printers()}


@app.post("/print")
async def print_file(printer: str = Form(...), file: UploadFile = File(...)):
    printers = installed_printers()
    if printer not in printers:
        raise HTTPException(status_code=400, detail="Selected printer is not installed on this PC")

    suffix = Path(file.filename or "document.pdf").suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".bmp"}:
        raise HTTPException(status_code=400, detail="Only PDF and image files are supported in this MVP")

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp.write(await file.read())
        temp.close()

        result = win32api.ShellExecute(
            0,
            "printto",
            temp.name,
            f'"{printer}"',
            ".",
            0,
        )

        if int(result) <= 32:
            raise RuntimeError(f"Windows print command failed with code {result}")

        return JSONResponse(
            {
                "success": True,
                "printer": printer,
                "file": file.filename,
                "message": "Print job sent to Windows",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    print(f"Phone USB Printer Bridge running on http://{local_ip()}:{APP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
