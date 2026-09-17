@echo off
setlocal
cd /d "%~dp0"
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-DevosPrintHotspot.ps1"
echo.
echo Press any key to close...
pause >nul
