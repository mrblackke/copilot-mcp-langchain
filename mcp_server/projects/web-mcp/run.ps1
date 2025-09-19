param([ValidateSet("start", "stop", "force-stop")][string]$Action = "start")

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".virtualenv\Scripts\activate.ps1"
if (Test-Path $VenvPath) { . $VenvPath } else { Write-Error "Virtual environment not found"; exit 1 }

function Force-Stop-Ports([int[]]$Ports) {
    foreach ($Port in $Ports) {
        Write-Host "Checking port $Port..." -ForegroundColor Yellow
        $PIDs = netstat -ano | findstr ":${Port}.*LISTENING" | ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
        if ($PIDs) {
            foreach ($ProcessID in $PIDs) {
                if ($ProcessID -and $ProcessID -gt 0) {
                    Write-Host "Killing process PID $ProcessID on port $Port" -ForegroundColor Yellow
                    $result = taskkill /PID $ProcessID /F 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[OK] Killed process PID $ProcessID" -ForegroundColor Green
                    } else {
                        Write-Host "[FAIL] Could not kill process PID $ProcessID" -ForegroundColor Red
                    }
                }
            }
        } else {
            Write-Host "No processes found on port $Port" -ForegroundColor Gray
        }
    }
}

switch ($Action) {
    "start" {
        Write-Host "Starting..." -ForegroundColor Green
        python -m mcp_server.run run lng_batch_run '{\"pipeline_file\": \"mcp_server/projects/web-mcp/config/stop_webhooks.json\"}'
        python -m mcp_server.run run --daemon lng_batch_run '{\"pipeline_file\": \"mcp_server/projects/web-mcp/config/start_webhooks.json\"}'
        Write-Host "Started! Web: http://localhost:8080/webhook | API: http://localhost:8081/execute" -ForegroundColor Cyan
    }
    "stop" {
        Write-Host "Stopping..." -ForegroundColor Yellow
        python -m mcp_server.run run lng_batch_run '{\"pipeline_file\": \"mcp_server/projects/web-mcp/config/stop_webhooks.json\"}'
        Write-Host "Stopped" -ForegroundColor Green
    }
    "force-stop" {
        Write-Host "Force stopping..." -ForegroundColor Red
        Force-Stop-Ports -Ports @(8080, 8081)
        Write-Host "Force stopped" -ForegroundColor Green
    }
}
