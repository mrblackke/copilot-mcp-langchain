param(
    [string]$BaseDirectory = "mcp_server/projects/telemetry/data"
)

# Получаем путь к корню проекта (3 уровня вверх от скрипта)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))

# Переходим в корень проекта
Set-Location $ProjectRoot

# Активируем виртуальное окружение
$VenvPath = Join-Path $ProjectRoot ".virtualenv\Scripts\activate.ps1"
if (Test-Path $VenvPath) {
    . $VenvPath
} else {
    Write-Error "Virtual environment not found at: $VenvPath"
    exit 1
}

# Запускаем Python команду
$json = '{\"pipeline_file\": \"mcp_server/projects/telemetry/pipeline/telemetry.json\", \"user_params\": {\"base_directory\": \"' + $BaseDirectory + '\"}}'
python -m mcp_server.run run lng_batch_run $json