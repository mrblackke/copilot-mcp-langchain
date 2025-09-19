import mcp.types as types
import os
import json
import requests
import re
from pathlib import Path

async def tool_info() -> dict:
    """Returns information about the lng_jira_download_attachments tool."""
    return {
        "description": """Downloads all attachments from a Jira ticket to a specified directory.

**Parameters:**
- `ticket_number` (string, required): Jira ticket number (e.g., "PROJ-123")
- `output_directory` (string, required): Directory to save downloaded attachments
- `env_file` (string, optional): Path to .env file (default: ".env")

**Environment Variables Required:**
- `JIRA_URL`: Base URL of your Jira instance (e.g., "https://yourcompany.atlassian.net")
- `JIRA_AUTH`: Bearer token for Jira API authentication

**Functionality:**
- Downloads all attachments from the specified ticket
- Sanitizes filenames to be filesystem-safe
- Creates output directory if it doesn't exist
- Provides detailed download progress and summary
- Handles various file types and sizes

**Returns:**
- List of successfully downloaded files with metadata
- Download summary including file names, sizes, and authors
- Error details for any failed downloads

**Example Usage:**
- Download all: `{"ticket_number": "PROJ-123", "output_directory": "./downloads"}`
- Custom env: `{"ticket_number": "PROJ-123", "output_directory": "./files", "env_file": ".env.local"}`

**Error Handling:**
- Creates directories as needed
- Handles permission and network errors
- Continues downloading other files if one fails
- Sanitizes filenames for cross-platform compatibility""",
        "schema": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "Jira ticket number (e.g., PROJ-123)"
                },
                "output_directory": {
                    "type": "string",
                    "description": "Directory to save downloaded attachments"
                },
                "env_file": {
                    "type": "string",
                    "description": "Optional: Path to .env file (default: .env)"
                }
            },
            "required": ["ticket_number", "output_directory"]
        }
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be safe for filesystem."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    
    # Limit length and strip whitespace
    filename = filename.strip()[:255]
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"
        
    return filename

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Downloads all attachments from a Jira ticket."""
    try:
        # Import dependencies
        try:
            from dotenv import load_dotenv
        except ImportError:
            error_result = {
                "success": False,
                "error": "Required dependency not available: python-dotenv. Please install python-dotenv."
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Extract parameters
        ticket_number = parameters.get("ticket_number", "")
        output_directory = parameters.get("output_directory", "")
        env_file = parameters.get("env_file", ".env")
        
        if not ticket_number:
            error_result = {
                "success": False,
                "error": "ticket_number parameter is required"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        if not output_directory:
            error_result = {
                "success": False,
                "error": "output_directory parameter is required"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Load environment variables
        env_path = os.path.expanduser(env_file)
        if not os.path.isabs(env_path):
            env_path = os.path.abspath(env_path)
            
        if not os.path.exists(env_path):
            error_result = {
                "success": False,
                "error": f".env file not found at {env_path}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Load .env file
        load_dotenv(env_path)
        
        # Get environment variables
        jira_url = os.getenv("JIRA_URL")
        jira_auth = os.getenv("JIRA_AUTH")
        
        if not jira_url:
            error_result = {
                "success": False,
                "error": "JIRA_URL not found in environment variables"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        if not jira_auth:
            error_result = {
                "success": False,
                "error": "JIRA_AUTH not found in environment variables"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Prepare output directory
        output_dir = os.path.expanduser(output_directory)
        if not os.path.isabs(output_dir):
            output_dir = os.path.abspath(output_dir)
        
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Failed to create output directory {output_dir}: {str(e)}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Get ticket information with attachments
        api_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ticket_number}"
        fields = "attachment,summary"
        full_url = f"{api_url}?fields={fields}"
        
        headers = {
            "Authorization": f"Bearer {jira_auth}",
            "Accept": "application/json"
        }
        
        try:
            # Get ticket data
            response = requests.get(full_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                if response.status_code == 401:
                    error_msg = "Authentication failed. Check your API token."
                elif response.status_code == 403:
                    error_msg = "Permission denied. Check if you have access to this ticket."
                elif response.status_code == 404:
                    error_msg = f"Ticket {ticket_number} not found. Check the ticket number."
                else:
                    error_msg = f"API request failed with status {response.status_code}"
                    
                error_result = {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
            ticket_data = response.json()
            
            # Check if ticket has attachments
            attachments = ticket_data.get("fields", {}).get("attachment", [])
            if not attachments:
                result = {
                    "success": True,
                    "operation": "jira_download_attachments",
                    "ticket_number": ticket_number,
                    "ticket_summary": ticket_data.get("fields", {}).get("summary", ""),
                    "output_directory": output_dir,
                    "message": "No attachments found for this ticket",
                    "downloaded_files": []
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            # Download each attachment
            downloaded_files = []
            failed_downloads = []
            
            for attachment in attachments:
                filename = sanitize_filename(attachment["filename"])
                file_path = os.path.join(output_dir, filename)
                
                try:
                    # Download attachment
                    download_response = requests.get(
                        attachment["content"], 
                        headers=headers, 
                        timeout=60,
                        stream=True
                    )
                    
                    if download_response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in download_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verify file was created and has correct size
                        if os.path.exists(file_path):
                            actual_size = os.path.getsize(file_path)
                            expected_size = int(attachment.get("size", 0))
                            
                            file_info = {
                                "filename": filename,
                                "original_filename": attachment["filename"],
                                "file_path": file_path,
                                "size_bytes": actual_size,
                                "expected_size_bytes": expected_size,
                                "mime_type": attachment.get("mimeType", "unknown"),
                                "author": attachment.get("author", {}).get("displayName", "Unknown"),
                                "created": attachment.get("created", ""),
                                "size_match": actual_size == expected_size
                            }
                            
                            downloaded_files.append(file_info)
                        else:
                            failed_downloads.append({
                                "filename": attachment["filename"],
                                "error": "File was not created after download"
                            })
                    else:
                        failed_downloads.append({
                            "filename": attachment["filename"],
                            "error": f"Download failed with status {download_response.status_code}"
                        })
                        
                except Exception as e:
                    failed_downloads.append({
                        "filename": attachment["filename"],
                        "error": f"Download error: {str(e)}"
                    })
            
            # Prepare result
            result = {
                "success": True,
                "operation": "jira_download_attachments",
                "ticket_number": ticket_number,
                "ticket_summary": ticket_data.get("fields", {}).get("summary", ""),
                "jira_url": jira_url,
                "output_directory": output_dir,
                "total_attachments": len(attachments),
                "downloaded_count": len(downloaded_files),
                "failed_count": len(failed_downloads),
                "downloaded_files": downloaded_files
            }
            
            if failed_downloads:
                result["failed_downloads"] = failed_downloads
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
            
        except requests.exceptions.Timeout:
            error_result = {
                "success": False,
                "error": "Request timeout. Check your network connection or Jira server availability."
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        except requests.exceptions.ConnectionError:
            error_result = {
                "success": False,
                "error": f"Connection error. Check if Jira URL is correct: {jira_url}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        except requests.exceptions.RequestException as e:
            error_result = {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
