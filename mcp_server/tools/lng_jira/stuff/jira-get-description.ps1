param(
    [Parameter(Mandatory=$true)]
    [string]$TicketNumber,
    
    [string]$EnvFile = ".env",
    [string]$OutputFile
)

# Function to load .env file
function Load-EnvFile {
    param([string]$FilePath)
    
    if (-Not (Test-Path $FilePath)) {
        Write-Host "Error: .env file not found at $FilePath" -ForegroundColor Red
        return $false
    }
    
    Get-Content $FilePath | ForEach-Object {
        if ($_ -match '^([^#][^=]*?)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove quotes if present
            $value = $value -replace '^["'']|["'']$', ''
            Set-Variable -Name $name -Value $value -Scope Script
            Write-Host "Loaded: $name" -ForegroundColor Green
        }
    }
    return $true
}

# Load environment variables
if (-Not (Load-EnvFile $EnvFile)) {
    exit 1
}

# Check required variables
if (-Not $JIRA_URL) {
    Write-Host "Error: JIRA_URL not found in .env file" -ForegroundColor Red
    exit 1
}

if (-Not $JIRA_AUTH) {
    Write-Host "Error: JIRA_AUTH not found in .env file" -ForegroundColor Red
    exit 1
}

Write-Host "Getting ticket data for: $TicketNumber" -ForegroundColor Green
Write-Host "Using Jira URL: $JIRA_URL" -ForegroundColor Cyan

$ApiUrl = "$JIRA_URL/rest/api/2/issue/$TicketNumber"
$Fields = "summary,description,status,assignee,reporter,created,updated,priority,issuetype"
$FullUrl = "$ApiUrl" + "?fields=$Fields"

Write-Host "Request URL: $FullUrl" -ForegroundColor Yellow

$Headers = @{
    "Authorization" = "Bearer $JIRA_AUTH"
    "Accept" = "application/json"
}

try {
    $Response = Invoke-RestMethod -Uri $FullUrl -Headers $Headers -Method Get
    $JsonOutput = $Response | ConvertTo-Json -Depth 5
    
    Write-Host "Success! Ticket data retrieved." -ForegroundColor Green
    
    if ($OutputFile) {
        $JsonOutput | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "Saved to file: $OutputFile" -ForegroundColor Green
    }
    
    return $JsonOutput
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    return $null
}
