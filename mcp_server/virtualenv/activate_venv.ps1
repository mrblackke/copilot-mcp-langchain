# Auto-activate virtual environment for this project
if (Test-Path "./.virtualenv/Scripts/Activate.ps1") {
    & "./.virtualenv/Scripts/Activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found at ./.virtualenv" -ForegroundColor Yellow
}
