@echo off
cd /d "%~dp0backend"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo [WARNING] No virtual environment found. Running with system Python.
)

echo Starting backend server (Uvicorn on http://127.0.0.1:8000)...
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
