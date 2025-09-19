param(
    [Parameter(Mandatory=$true)]
    [string]$TicketNumber,
    
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [string]$EnvFile = ".env",
    [string]$Comment = ""
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

# Check if file exists
if (-Not (Test-Path $FilePath)) {
    Write-Host "Error: File not found at $FilePath" -ForegroundColor Red
    exit 1
}

$fileInfo = Get-Item $FilePath
$fileName = $fileInfo.Name
$fileSizeKB = [math]::Round($fileInfo.Length / 1024, 2)

Write-Host "Uploading file to ticket: $TicketNumber" -ForegroundColor Green
Write-Host "Using Jira URL: $JIRA_URL" -ForegroundColor Cyan
Write-Host "File: $fileName ($fileSizeKB KB)" -ForegroundColor Cyan

# Jira attachment API endpoint
$ApiUrl = "$JIRA_URL/rest/api/2/issue/$TicketNumber/attachments"

Write-Host "Upload URL: $ApiUrl" -ForegroundColor Yellow

# Headers for file upload
$Headers = @{
    "Authorization" = "Bearer $JIRA_AUTH"
    "X-Atlassian-Token" = "no-check"  # Required to prevent CSRF errors
}

try {
    # Upload file using .NET WebClient for PowerShell 5.1 compatibility
    Write-Host "Uploading file..." -ForegroundColor Cyan
    
    # Create boundary for multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    # Read file content
    $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
    
    # Create multipart form data content manually
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
        "Content-Type: application/octet-stream",
        "",
        ""
    )
    
    $bodyStart = ($bodyLines -join $LF) + $LF
    $bodyEnd = $LF + "--$boundary--" + $LF
    
    # Convert strings to bytes
    $bodyStartBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyStart)
    $bodyEndBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyEnd)
    
    # Combine all bytes
    $totalLength = $bodyStartBytes.Length + $fileBytes.Length + $bodyEndBytes.Length
    $bodyBytes = New-Object byte[] $totalLength
    
    [System.Array]::Copy($bodyStartBytes, 0, $bodyBytes, 0, $bodyStartBytes.Length)
    [System.Array]::Copy($fileBytes, 0, $bodyBytes, $bodyStartBytes.Length, $fileBytes.Length)
    [System.Array]::Copy($bodyEndBytes, 0, $bodyBytes, $bodyStartBytes.Length + $fileBytes.Length, $bodyEndBytes.Length)
    
    # Create WebClient
    $webClient = New-Object System.Net.WebClient
    $webClient.Headers.Add("Authorization", "Bearer $JIRA_AUTH")
    $webClient.Headers.Add("X-Atlassian-Token", "no-check")
    $webClient.Headers.Add("Content-Type", "multipart/form-data; boundary=$boundary")
    
    try {
        # Upload the file
        $responseBytes = $webClient.UploadData($ApiUrl, "POST", $bodyBytes)
        $responseString = [System.Text.Encoding]::UTF8.GetString($responseBytes)
        
        try {
            $jsonResponse = $responseString | ConvertFrom-Json
            
            Write-Host "Successfully uploaded file!" -ForegroundColor Green
            
            # Display upload results
            Write-Host "`n=== UPLOAD SUMMARY ===" -ForegroundColor Green
            Write-Host "Ticket: $TicketNumber" -ForegroundColor White
            Write-Host "Uploaded file: $fileName" -ForegroundColor White
            Write-Host "File size: $fileSizeKB KB" -ForegroundColor White
            
            if ($jsonResponse -and $jsonResponse.Count -gt 0) {
                Write-Host "`nAttachment details:" -ForegroundColor Yellow
                foreach ($attachment in $jsonResponse) {
                    Write-Host "  - ID: $($attachment.id)" -ForegroundColor White
                    Write-Host "    Filename: $($attachment.filename)" -ForegroundColor White
                    Write-Host "    Size: $($attachment.size) bytes" -ForegroundColor White
                    Write-Host "    MIME Type: $($attachment.mimeType)" -ForegroundColor White
                    Write-Host "    Author: $($attachment.author.displayName)" -ForegroundColor White
                    Write-Host "    Created: $($attachment.created)" -ForegroundColor White
                    Write-Host "    Download URL: $($attachment.content)" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Host "File uploaded but failed to parse response" -ForegroundColor Yellow
            Write-Host "Raw response: $responseString" -ForegroundColor Gray
        }
    }
    catch {
        $errorMessage = $_.Exception.Message
        Write-Host "Error uploading file: $errorMessage" -ForegroundColor Red
        
        # Check for common error patterns
        if ($errorMessage -match "401") {
            Write-Host "Authentication failed. Check your API token." -ForegroundColor Yellow
        }
        elseif ($errorMessage -match "403") {
            Write-Host "Permission denied. Check if you have permission to add attachments." -ForegroundColor Yellow
        }
        elseif ($errorMessage -match "404") {
            Write-Host "Ticket not found. Check the ticket number." -ForegroundColor Yellow
        }
        elseif ($errorMessage -match "413") {
            Write-Host "File may be too large. Check Jira attachment size limits." -ForegroundColor Yellow
        }
        
        throw "File upload failed: $errorMessage"
    }
    finally {
        $webClient.Dispose()
    }
    
    # Add comment if provided
    if ($Comment) {
        Write-Host "`nAdding comment..." -ForegroundColor Cyan
        
        $CommentApiUrl = "$JIRA_URL/rest/api/2/issue/$TicketNumber/comment"
        $CommentBody = @{
            body = $Comment
        } | ConvertTo-Json
        
        $CommentHeaders = @{
            "Authorization" = "Bearer $JIRA_AUTH"
            "Content-Type" = "application/json"
        }
        
        try {
            $CommentResponse = Invoke-RestMethod -Uri $CommentApiUrl -Headers $CommentHeaders -Method Post -Body $CommentBody
            Write-Host "Comment added successfully" -ForegroundColor Green
        }
        catch {
            Write-Host "Warning: Failed to add comment - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "Error uploading file: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
        
        # Check for common errors
        if ($responseBody -match "413") {
            Write-Host "File may be too large. Check Jira attachment size limits." -ForegroundColor Yellow
        }
        elseif ($responseBody -match "401") {
            Write-Host "Authentication failed. Check your API token." -ForegroundColor Yellow
        }
        elseif ($responseBody -match "403") {
            Write-Host "Permission denied. Check if you have permission to add attachments." -ForegroundColor Yellow
        }
        elseif ($responseBody -match "404") {
            Write-Host "Ticket not found. Check the ticket number." -ForegroundColor Yellow
        }
    }
    exit 1
}
