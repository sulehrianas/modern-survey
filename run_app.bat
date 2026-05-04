@echo off
cd /d "%~dp0"

echo Checking for virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo Found .venv, using it.
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    ".venv\Scripts\python.exe" main.py
) else (
    echo .venv not found, using system Python.
    pip install -r requirements.txt
    python main.py
)
pause