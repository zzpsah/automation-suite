@echo off
setlocal
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --name PhonePrinterBridge print_server.py

echo.
echo Build complete. EXE is in dist\PhonePrinterBridge.exe
endlocal
