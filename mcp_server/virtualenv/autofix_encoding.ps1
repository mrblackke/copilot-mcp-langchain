# PowerShell Auto-Fix for Encoding Bug (Compact Version)
# Automatically fixes commands that start with Cyrillic "s" (U+0441 = 1089)

$ExecutionContext.InvokeCommand.CommandNotFoundAction = {
    param($CommandName, $CommandLookupEventArgs)
    
    # Check if command starts with Cyrillic "s" (Unicode 1089)
    if ($CommandName.Length -gt 0 -and [int][char]$CommandName[0] -eq 1089) {
        $FixedCommand = $CommandName.Substring(1)
        Write-Host "Auto-fixing: '$CommandName' -> '$FixedCommand'" -ForegroundColor Yellow
        
        # Try to find the fixed command
        $Command = Get-Command $FixedCommand -ErrorAction SilentlyContinue
        if ($Command) {
            $CommandLookupEventArgs.CommandScriptBlock = [ScriptBlock]::Create("& '$FixedCommand' @args")
            Write-Host "Fixed successfully" -ForegroundColor Green
        } else {
            Write-Host "Command '$FixedCommand' not found" -ForegroundColor Red
        }
    }
}

Write-Host "PowerShell encoding auto-fix loaded" -ForegroundColor Cyan
