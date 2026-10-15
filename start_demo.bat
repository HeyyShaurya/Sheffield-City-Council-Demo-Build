@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Preparing isolated Python environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Unable to create environment. Install Python 3.11 or newer and retry.
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check Python and internet connection.
    pause
    exit /b 1
)
echo.
echo SHEFFIELD CONNECT: open http://127.0.0.1:8000
 echo Access code: sheffield-demo (unless SHEFFIELD_DEMO_PIN was changed)
echo Keep this window open during your demo. Ctrl+C stops the server.
echo.
".venv\Scripts\python.exe" run.py
pause
