@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0stop-dev.ps1"
if %errorlevel% neq 0 (
    echo Failed to stop services. Please check the output above.
)
pause
