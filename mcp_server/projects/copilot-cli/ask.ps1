param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Command,
    
    [Parameter(Position=1, Mandatory=$false)]
    [string]$Question
)

# Function to ensure virtual environment is activated
function Ensure-VirtualEnv {
    $venvPath = "$PSScriptRoot\..\.virtualenv"
    $activateScript = "$venvPath\Scripts\Activate.ps1"
    
    # Check if virtual environment is already active
    if (-not $env:VIRTUAL_ENV) {
        if (Test-Path $activateScript) {
            Write-Host "Activating virtual environment..." -ForegroundColor Cyan
            & $activateScript
        } else {
            Write-Host "Error: Virtual environment not found at $venvPath" -ForegroundColor Red
            exit 1
        }
    }
}

# Function to display usage examples
function Show-UsageExamples {
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Yellow
    Write-Host "  ask help" -NoNewline -ForegroundColor Cyan; Write-Host "                              " -NoNewline -ForegroundColor Cyan; Write-Host "# Show help information" -ForegroundColor Green
    Write-Host "  ask " -NoNewline -ForegroundColor Cyan; Write-Host '"What is Git?"' -NoNewline -ForegroundColor Cyan; Write-Host "                    " -NoNewline -ForegroundColor Cyan; Write-Host "# Ask AI directly" -ForegroundColor Green
    Write-Host "  ask " -NoNewline -ForegroundColor Cyan; Write-Host '"dir" "How many files?"' -NoNewline -ForegroundColor Cyan; Write-Host "           " -NoNewline -ForegroundColor Cyan; Write-Host "# Run command, ask AI about result" -ForegroundColor Green
    Write-Host "  ask " -NoNewline -ForegroundColor Cyan; Write-Host '"Get-Process" "Top memory usage?"' -NoNewline -ForegroundColor Cyan; Write-Host " " -NoNewline -ForegroundColor Cyan; Write-Host " " -ForegroundColor Green
    Write-Host "  ask uninstall" -NoNewline -ForegroundColor Cyan; Write-Host "                         " -NoNewline -ForegroundColor Cyan; Write-Host "# Remove global command" -ForegroundColor Green
}

# Function to find project root directory
function Find-ProjectRoot {
    param([string]$StartPath = $PSScriptRoot)
    
    $currentPath = $StartPath
    $maxDepth = 10 # Prevent infinite loop
    $depth = 0
    
    while ($depth -lt $maxDepth) {
        # Look for indicators of project root
        $indicators = @("mcp_server")
        
        foreach ($indicator in $indicators) {
            $testPath = Join-Path $currentPath $indicator
            if (Test-Path $testPath) {
                # Write-Host "Found project root at: $currentPath" -ForegroundColor Cyan
                return $currentPath
            }
        }
        
        # Move up one directory
        $parentPath = Split-Path $currentPath -Parent
        if ($parentPath -eq $currentPath) {
            # Reached root drive, stop
            break
        }
        $currentPath = $parentPath
        $depth++
    }
    
    # If not found, try current script directory as fallback
    Write-Host "Project root not found, using script directory: $PSScriptRoot" -ForegroundColor Yellow
    return $PSScriptRoot
}

# Function to get system information
function Get-SystemInfo {
    # Disable progress bar for system info gathering
    $ProgressPreference = 'SilentlyContinue'
    
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
    $computerInfo = Get-ComputerInfo -Property WindowsProductName, WindowsVersion, TotalPhysicalMemory -ErrorAction SilentlyContinue
    
    $systemInfo = @"
System Context:
- OS: $($osInfo.Caption) (Build $($osInfo.BuildNumber))
- PowerShell Version: $($PSVersionTable.PSVersion)
- Console: Windows PowerShell Terminal
- Architecture: $($env:PROCESSOR_ARCHITECTURE)
- Current Directory: $($PWD.Path)
"@
    
    return $systemInfo
}

# Function to install PowerShell alias
function Install-AskAlias {
    $ASK_SCRIPT_PATH = $PSCommandPath
    $ASK_PROFILE = Join-Path -Path $(Split-Path -Path $PROFILE -Parent) -ChildPath "ask-alias.ps1"

    # Create the alias profile script
    $aliasContent = @"
# Ask Terminal Chat Function
# Generated automatically by ask.ps1 install

function ask {
    param(
        [Parameter(Position=0, Mandatory=`$false)]
        [string]`$Command,
        
        [Parameter(Position=1, Mandatory=`$false)]
        [string]`$Question
    )
    
    `$askScriptPath = "$ASK_SCRIPT_PATH"
    
    if (-not (Test-Path `$askScriptPath)) {
        Write-Host "Error: ask.ps1 script not found at `$askScriptPath" -ForegroundColor Red
        Write-Host "Please make sure the ask.ps1 script is available at the correct location." -ForegroundColor Yellow
        return
    }
    
    if (`$Command -and `$Question) {
        # Command analysis mode
        & `$askScriptPath `$Command `$Question
    } elseif (`$Command) {
        # Simple question mode or special commands
        if (`$Command -eq "install") {
            & `$askScriptPath install
        } elseif (`$Command -eq "uninstall") {
            & `$askScriptPath uninstall
        } elseif (`$Command -eq "help") {
            & `$askScriptPath help
        } else {
            & `$askScriptPath `$Command
        }
    } else {
        # Show usage if no parameters
        & `$askScriptPath help
    }
}

Write-Host "Ask Terminal Chat function loaded. Use " -NoNewline -ForegroundColor Cyan; Write-Host "'ask help'" -NoNewline -ForegroundColor Yellow; Write-Host " for more information." -ForegroundColor Cyan
"@

    # Write the alias content to the profile file
    Write-Host "Creating ask alias profile at: $ASK_PROFILE" -ForegroundColor Cyan
    $aliasContent | Out-File -FilePath $ASK_PROFILE -Encoding UTF8 -Force

    # Check if PROFILE exists, create if not
    if (-not (Test-Path $PROFILE)) {
        Write-Host "Creating PowerShell profile at: $PROFILE" -ForegroundColor Cyan
        New-Item -Path $PROFILE -ItemType File -Force | Out-Null
    }

    # Check if our alias is already sourced in the profile
    $profileContent = Get-Content $PROFILE -ErrorAction SilentlyContinue
    $sourceCommand = ". `"$ASK_PROFILE`""

    if ($profileContent -notcontains $sourceCommand) {
        Write-Host "Adding ask alias to PowerShell profile..." -ForegroundColor Cyan
        Add-Content -Path $PROFILE -Value $sourceCommand -Encoding UTF8
        Write-Host "Ask alias added to profile successfully!" -ForegroundColor Cyan
    } else {
        Write-Host "Ask alias already exists in profile." -ForegroundColor Cyan
    }

    Write-Host "Installation complete!" -ForegroundColor Cyan
    
    # Automatically load the alias in the current session
    Write-Host "Loading ask function in current session..." -ForegroundColor Cyan
    try {
        . $ASK_PROFILE
    } catch {
        Write-Host "Warning: Could not load alias automatically. Please restart PowerShell." -ForegroundColor Cyan
        Write-Host "Or run manually: . `"$ASK_PROFILE`"" -ForegroundColor Cyan
    }
        
    Show-UsageExamples
    
    Write-Host ""
    Write-Host "Please restart your PowerShell session for changes to take effect." -ForegroundColor Yellow

    exit 0
}

# Function to uninstall PowerShell alias
function Uninstall-AskAlias {
    $ASK_PROFILE = Join-Path -Path $(Split-Path -Path $PROFILE -Parent) -ChildPath "ask-alias.ps1"
    $sourceCommand = ". `"$ASK_PROFILE`""

    Write-Host "Removing ask alias..." -ForegroundColor Cyan

    # Remove the alias profile file
    if (Test-Path $ASK_PROFILE) {
        Remove-Item $ASK_PROFILE -Force
        Write-Host "Removed ask alias profile: $ASK_PROFILE" -ForegroundColor Cyan
    } else {
        Write-Host "Ask alias profile not found: $ASK_PROFILE" -ForegroundColor Cyan
    }

    # Remove the source command from PowerShell profile
    if (Test-Path $PROFILE) {
        $profileContent = Get-Content $PROFILE
        $newContent = $profileContent | Where-Object { $_ -ne $sourceCommand }
        
        if ($profileContent.Count -ne $newContent.Count) {
            $newContent | Out-File -FilePath $PROFILE -Encoding UTF8 -Force
            Write-Host "Removed ask alias from PowerShell profile." -ForegroundColor Cyan
        } else {
            Write-Host "Ask alias not found in PowerShell profile." -ForegroundColor Cyan
        }
    } else {
        Write-Host "PowerShell profile not found: $PROFILE" -ForegroundColor Cyan
    }

    Write-Host "Uninstallation complete!" -ForegroundColor Cyan
    Write-Host "Please restart your PowerShell session for changes to take effect." -ForegroundColor Yellow
    
    exit 0
}

# Check for special commands first
if ($Command -eq "install") {
    Install-AskAlias
} elseif ($Command -eq "uninstall") {
    Uninstall-AskAlias
} elseif ($Command -eq "help" -or -not $Command) {
    # Show help message
    Write-Host "Ask Terminal Chat - AI assistant for command line" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This tool helps you get answers about commands and general questions using AI." -ForegroundColor White
    Write-Host "System context (OS, shell, directory) is automatically included for better answers." -ForegroundColor White
    Write-Host ""
    Write-Host "Installation:" -ForegroundColor Yellow
    Write-Host "  ./ask.ps1 install" -NoNewline -ForegroundColor Cyan; Write-Host "                     " -NoNewline -ForegroundColor Cyan; Write-Host "# Install global 'ask' command (recommended)" -ForegroundColor Green
    
    Show-UsageExamples
    exit 0
}

# Ensure virtual environment is activated (only for normal operation)
Ensure-VirtualEnv

# Set console encoding to UTF-8 to handle Unicode properly
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Color functions
function Write-ColoredText {
    param(
        [string]$Message,
        [string]$Color
    )
    Write-Host $Message -ForegroundColor $Color
}

# Check if this is a simple question mode (only one parameter)
if (-not $Question) {
    # Simple question mode - first parameter is actually the question
    $actualQuestion = $Command
    
    Write-Host "Question: $actualQuestion" -ForegroundColor Yellow
    
    # Change to the project root directory to find mcp_server module
    $originalLocation = Get-Location
    $projectRoot = Find-ProjectRoot
    Set-Location $projectRoot
    
    # Create a temporary file with simple question for LLM
    $tempFile = [System.IO.Path]::GetTempFileName()
    
    # Create JSON object for simple LLM query with special prompt
    $systemInfo = Get-SystemInfo
    $jsonObject = @{
        command = "echo 'Simple question mode'"
        command_output = "This is a direct question to the LLM without executing any command."
        question = $actualQuestion
        system_info = $systemInfo
    }
    
    # Convert to JSON and save to temp file
    $jsonContent = $jsonObject | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($tempFile, $jsonContent, [System.Text.Encoding]::UTF8)
    
    # Fix path for Python (replace backslashes with forward slashes)
    $pythonTempFile = $tempFile -replace '\\', '/'
    
    # Call MCP tool by reading JSON from temp file (using utf-8-sig to handle BOM)
    $response = & python -c "import json; import sys; data=json.load(open('$pythonTempFile', 'r', encoding='utf-8-sig')); import subprocess; result=subprocess.run([sys.executable, '-m', 'mcp_server.run', 'run', 'lng_terminal_chat', json.dumps(data)], capture_output=True, text=True, encoding='utf-8'); print(result.stdout); print(result.stderr, file=sys.stderr); sys.exit(result.returncode)" 2>&1
    $mcpExitCode = $LASTEXITCODE
    
    # Cleanup temp file and return to original location
    Remove-Item $tempFile -Force
    Set-Location $originalLocation
    
    if ($mcpExitCode -ne 0) {
        Write-ColoredText "Error: $response" "Red"
        exit 1
    }
    
    # Extract just the result from the MCP output (remove debug info)
    $lines = $response -split "`n"
    $resultStarted = $false
    $result = ""
    
    foreach ($line in $lines) {
        if ($line -match "Result:") {
            $resultStarted = $true
            $result = $line -replace ".*Result:\s*", ""
            continue
        }
        if ($resultStarted -and $line.Trim() -ne "") {
            if ($result -ne "") {
                $result += "`n"
            }
            $result += $line
        }
    }
    
    # If we couldn't parse the result, use the full response
    if ($result.Trim() -eq "") {
        $result = $response
    }
    
    # Display the answer with "Answer:" prefix in green
    Write-ColoredText "Answer: $($result.Trim())" "Green"
    exit 0
}

# Standard command + question mode
if (-not $Command -or -not $Question) {
    Write-ColoredText "Usage:" "Red"
    Write-ColoredText "  .\gpt.ps1 '<question>'                    # Simple question mode" "Yellow"
    Write-ColoredText "  .\gpt.ps1 '<command>' '<question>'        # Command analysis mode" "Yellow"
    Write-ColoredText "Examples:" "Cyan"
    Write-ColoredText "  .\gpt.ps1 'What is the capital of France?'" "Cyan"
    Write-ColoredText "  .\gpt.ps1 'docker ps -a' 'How many containers are running?'" "Cyan"
    exit 1
}

try {
    # Display the question with "Question:" prefix in yellow
    Write-Host "Question: $Question" -ForegroundColor Yellow
    
    # Display the command with ">" prefix in blue
    Write-ColoredText "> $Command" "Blue"
    
    # Execute command and capture output
    $output = Invoke-Expression $Command 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    
    # Display the command output in light cyan (more light blue)
    Write-ColoredText $output.Trim() "White"
    
    # Change to the project root directory to find mcp_server module
    $originalLocation = Get-Location
    $projectRoot = Find-ProjectRoot
    Set-Location $projectRoot
    
    # Create a temporary file with JSON parameters to avoid escaping issues
    $tempFile = [System.IO.Path]::GetTempFileName()
    
    # Create JSON object with three separate parameters
    $systemInfo = Get-SystemInfo
    $jsonObject = @{
        command = $Command
        command_output = $output.Trim()
        question = $Question
        system_info = $systemInfo
    }
    
    # Convert to JSON and save to temp file
    $jsonContent = $jsonObject | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($tempFile, $jsonContent, [System.Text.Encoding]::UTF8)
    
    # Fix path for Python (replace backslashes with forward slashes)
    $pythonTempFile = $tempFile -replace '\\', '/'
    
    # Call MCP tool by reading JSON from temp file (using utf-8-sig to handle BOM)
    $response = & python -c "import json; import sys; data=json.load(open('$pythonTempFile', 'r', encoding='utf-8-sig')); import subprocess; result=subprocess.run([sys.executable, '-m', 'mcp_server.run', 'run', 'lng_terminal_chat', json.dumps(data)], capture_output=True, text=True, encoding='utf-8'); print(result.stdout); print(result.stderr, file=sys.stderr); sys.exit(result.returncode)" 2>&1
    $mcpExitCode = $LASTEXITCODE
    
    # Cleanup temp file and return to original location
    Remove-Item $tempFile -Force
    Set-Location $originalLocation
    
    if ($mcpExitCode -ne 0) {
        Write-ColoredText "Error: $response" "Red"
        exit 1
    }
    
    # Extract just the result from the MCP output (remove debug info)
    $lines = $response -split "`n"
    $resultStarted = $false
    $result = ""
    
    foreach ($line in $lines) {
        if ($line -match "Result:") {
            $resultStarted = $true
            $result = $line -replace ".*Result:\s*", ""
            continue
        }
        if ($resultStarted -and $line.Trim() -ne "") {
            if ($result -ne "") {
                $result += "`n"
            }
            $result += $line
        }
    }
    
    # If we couldn't parse the result, use the full response
    if ($result.Trim() -eq "") {
        $result = $response
    }
    
    # Display the answer with "Answer:" prefix in green
    Write-ColoredText "Answer: $($result.Trim())" "Green"
}
catch {
    Write-ColoredText "Error executing command: $($_.Exception.Message)" "Red"
    exit 1
}
