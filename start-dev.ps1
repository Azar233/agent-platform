# VisionPay Agent - 启动开发环境（单窗口后台模式）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir = $PSScriptRoot
$RuntimeDir = Join-Path $ScriptDir ".runtime"
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"
$BackendLog = Join-Path $RuntimeDir "backend.log"
$FrontendLog = Join-Path $RuntimeDir "frontend.log"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "VisionPay Agent - 启动开发环境" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 同时启动后端和前端，不弹新窗口，日志写入文件
Write-Host "[1/2] 启动后端服务 (http://127.0.0.1:8000) ..."
$backend = Start-Process powershell `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $BackendLog `
    -ArgumentList "-Command", "cd '$BackendDir'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --host 127.0.0.1 --port 8000 --reload 2>&1"
$backend.Id | Out-File (Join-Path $RuntimeDir "backend.pid") -Encoding utf8

Write-Host "[2/2] 启动前端服务 (http://127.0.0.1:5173) ..."
$frontend = Start-Process powershell `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $FrontendLog `
    -ArgumentList "-Command", "cd '$FrontendDir'; npm run dev -- --host 127.0.0.1 2>&1"
$frontend.Id | Out-File (Join-Path $RuntimeDir "frontend.pid") -Encoding utf8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "服务已启动" -ForegroundColor Green
Write-Host "后端:    http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "前端:    http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "API文档: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "日志:    $RuntimeDir" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "提示: 运行 .\stop-dev.cmd 停止服务" -ForegroundColor Yellow
