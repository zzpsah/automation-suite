@echo off
setlocal
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --noconsole --name PhonePrinterBridge ^
  --collect-submodules uvicorn ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan.on ^
  --collect-all win32print ^
  --collect-all win32timezone ^
  --hidden-import win32timezone ^
  admin_gui.py

echo.
echo Build complete. EXE is in dist\PhonePrinterBridge.exe
endlocal
