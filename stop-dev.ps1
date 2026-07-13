# VisionPay Agent - 停止开发环境
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir = $PSScriptRoot
$RuntimeDir = Join-Path $ScriptDir ".runtime"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "VisionPay Agent - 停止开发环境" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

function Stop-ByPidFile($name, $pidFile) {
    if (Test-Path $pidFile) {
        $pidValue = (Get-Content $pidFile -Raw).Trim()
        if ([string]::IsNullOrWhiteSpace($pidValue)) {
            Write-Host "$name 的 PID 文件为空，尝试按端口停止..." -ForegroundColor Yellow
            Remove-Item $pidFile -Force
            return
        }
        $result = Start-Process taskkill -ArgumentList "/T", "/F", "/PID", $pidValue -Wait -NoNewWindow -PassThru
        if ($result.ExitCode -eq 0) {
            Write-Host "已停止 $name (PID: $pidValue)" -ForegroundColor Green
        } else {
            Write-Host "$name 进程可能已停止 (PID: $pidValue)" -ForegroundColor Yellow
        }
        Remove-Item $pidFile -Force
    } else {
        Write-Host "未找到 $name 的 PID 文件，尝试按端口停止..." -ForegroundColor Yellow
    }
}

Stop-ByPidFile "后端" (Join-Path $RuntimeDir "backend.pid")
Stop-ByPidFile "前端" (Join-Path $RuntimeDir "frontend.pid")

# 兜底：按端口清理剩余进程
$ports = @(8000, 5173)
foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.OwningProcess -ne 0) {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "已停止端口 $port 上的进程 (PID: $($_.OwningProcess))" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
