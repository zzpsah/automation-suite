@echo off
setlocal
cd /d "%~dp0"
python gui.py
if errorlevel 1 (
  echo.
  echo GUI failed to start. Make sure Python is installed and available in PATH.
  pause
)
