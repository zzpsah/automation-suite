@echo off
setlocal
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --noconsole --name PhonePrinterBridge admin_gui.py

echo.
echo Build complete. EXE is in dist\PhonePrinterBridge.exe
endlocal
