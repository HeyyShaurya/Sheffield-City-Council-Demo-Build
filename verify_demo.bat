@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run start_demo.bat to prepare Python dependencies.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install pytest httpx
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" scripts\verify_demo.py
pause
