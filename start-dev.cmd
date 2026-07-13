@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1"
if %errorlevel% neq 0 (
    echo Failed to start services. Please check the output above.
)
pause
