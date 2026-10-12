@echo off
cd /d "%~dp0"
if exist "PhotoForge3D-PC.exe" (
    start "" "PhotoForge3D-PC.exe"
) else (
    ".venv\Scripts\pythonw.exe" "launch_pc.py"
)
