@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First open this folder in VS Code and follow START_HERE.md.
  echo The Python environment has not been created yet.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" server.py
pause
