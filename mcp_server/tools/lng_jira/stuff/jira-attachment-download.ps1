param(
    [Parameter(Mandatory=$true)]
    [string]$TicketNumber,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputDirectory,
    
    [string]$EnvFile = ".env"
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

# Function to create directory if it doesn't exist
function Ensure-Directory {
    param([string]$Path)
    
    if (-Not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Created directory: $Path" -ForegroundColor Green
    }
}

# Function to sanitize filename
function Get-SafeFileName {
    param([string]$FileName)
    
    $invalidChars = [IO.Path]::GetInvalidFileNameChars() -join ''
    $pattern = "[{0}]" -f [regex]::Escape($invalidChars)
    return $FileName -replace $pattern, '_'
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

Write-Host "Getting attachments for ticket: $TicketNumber" -ForegroundColor Green
Write-Host "Using Jira URL: $JIRA_URL" -ForegroundColor Cyan
Write-Host "Output directory: $OutputDirectory" -ForegroundColor Cyan

# Ensure output directory exists
Ensure-Directory $OutputDirectory

# Get ticket information with attachments
$ApiUrl = "$JIRA_URL/rest/api/2/issue/$TicketNumber"
$Fields = "attachment,summary"
$FullUrl = "$ApiUrl" + "?fields=$Fields"

Write-Host "Request URL: $FullUrl" -ForegroundColor Yellow

$Headers = @{
    "Authorization" = "Bearer $JIRA_AUTH"
    "Accept" = "application/json"
}

try {
    $Response = Invoke-RestMethod -Uri $FullUrl -Headers $Headers -Method Get
    
    if (-Not $Response.fields.attachment -or $Response.fields.attachment.Count -eq 0) {
        Write-Host "No attachments found for ticket $TicketNumber" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Found $($Response.fields.attachment.Count) attachments" -ForegroundColor Green
    
    $downloadedFiles = @()
    
    foreach ($attachment in $Response.fields.attachment) {
        $fileName = Get-SafeFileName $attachment.filename
        $filePath = Join-Path $OutputDirectory $fileName
        
        Write-Host "Downloading: $fileName ($($attachment.size) bytes)" -ForegroundColor Cyan
        
        try {
            # Download attachment
            Invoke-WebRequest -Uri $attachment.content -Headers $Headers -OutFile $filePath
            Write-Host "Downloaded: $fileName" -ForegroundColor Green
            
            $downloadedFiles += @{
                FileName = $fileName
                FilePath = $filePath
                Size = $attachment.size
                MimeType = $attachment.mimeType
                Author = $attachment.author.displayName
                Created = $attachment.created
            }
        }
        catch {
            Write-Host "Failed to download: $fileName - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Summary
    Write-Host "`n=== DOWNLOAD SUMMARY ===" -ForegroundColor Green
    Write-Host "Ticket: $TicketNumber - $($Response.fields.summary)" -ForegroundColor White
    Write-Host "Total files downloaded: $($downloadedFiles.Count)" -ForegroundColor White
    Write-Host "Output directory: $OutputDirectory" -ForegroundColor White
    
    if ($downloadedFiles.Count -gt 0) {
        Write-Host "`nDownloaded files:" -ForegroundColor Yellow
        foreach ($file in $downloadedFiles) {
            $sizeKB = [math]::Round($file.Size / 1024, 2)
            Write-Host "  - $($file.FileName) ($sizeKB KB) - $($file.MimeType)" -ForegroundColor White
            Write-Host "    Author: $($file.Author), Created: $($file.Created)" -ForegroundColor Gray
        }
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
    exit 1
}
