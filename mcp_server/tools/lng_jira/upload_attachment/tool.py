import mcp.types as types
import os
import json
import requests
from pathlib import Path

async def tool_info() -> dict:
    """Returns information about the lng_jira_upload_attachment tool."""
    return {
        "description": """Uploads a file as an attachment to a Jira ticket with optional comment.

**Parameters:**
- `ticket_number` (string, required): Jira ticket number (e.g., "PROJ-123")
- `file_path` (string, required): Path to the file to upload
- `comment` (string, optional): Comment to add when uploading the attachment
- `env_file` (string, optional): Path to .env file (default: ".env")

**Environment Variables Required:**
- `JIRA_URL`: Base URL of your Jira instance (e.g., "https://yourcompany.atlassian.net")
- `JIRA_AUTH`: Bearer token for Jira API authentication

**Functionality:**
- Uploads any file type as attachment to Jira ticket
- Validates file existence and readability before upload
- Optionally adds a comment to the ticket explaining the upload
- Handles various file sizes (respects Jira limits)
- Returns detailed upload confirmation with attachment metadata

**Returns:**
- Upload success confirmation with attachment details
- Attachment ID, filename, size, MIME type, author, and creation date
- Download URL for the uploaded attachment
- Error details if upload fails

**Example Usage:**
- Upload file: `{"ticket_number": "PROJ-123", "file_path": "document.pdf"}`
- With comment: `{"ticket_number": "PROJ-123", "file_path": "image.png", "comment": "Screenshot of the issue"}`

**Error Handling:**
- Validates file existence and permissions
- Handles authentication and authorization errors
- Provides specific error messages for common issues
- Respects Jira file size limits""",
        "schema": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "Jira ticket number (e.g., PROJ-123)"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to upload"
                },
                "comment": {
                    "type": "string",
                    "description": "Optional comment to add when uploading"
                },
                "env_file": {
                    "type": "string",
                    "description": "Optional: Path to .env file (default: .env)"
                }
            },
            "required": ["ticket_number", "file_path"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Uploads a file as an attachment to a Jira ticket."""
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
        file_path = parameters.get("file_path", "")
        comment = parameters.get("comment", "")
        env_file = parameters.get("env_file", ".env")
        
        if not ticket_number:
            error_result = {
                "success": False,
                "error": "ticket_number parameter is required"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        if not file_path:
            error_result = {
                "success": False,
                "error": "file_path parameter is required"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Validate file
        file_path_expanded = os.path.expanduser(file_path)
        if not os.path.isabs(file_path_expanded):
            file_path_expanded = os.path.abspath(file_path_expanded)
            
        if not os.path.exists(file_path_expanded):
            error_result = {
                "success": False,
                "error": f"File not found: {file_path_expanded}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
        if not os.path.isfile(file_path_expanded):
            error_result = {
                "success": False,
                "error": f"Path is not a file: {file_path_expanded}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Get file info
        try:
            file_size = os.path.getsize(file_path_expanded)
            file_name = os.path.basename(file_path_expanded)
            file_size_kb = round(file_size / 1024, 2)
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Failed to read file info: {str(e)}"
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
        
        # Prepare upload URL
        upload_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ticket_number}/attachments"
        
        headers = {
            "Authorization": f"Bearer {jira_auth}",
            "X-Atlassian-Token": "no-check"  # Required to prevent CSRF errors
        }
        
        try:
            # Upload file
            with open(file_path_expanded, 'rb') as file_content:
                files = {
                    'file': (file_name, file_content, 'application/octet-stream')
                }
                
                upload_response = requests.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    timeout=120  # Longer timeout for file uploads
                )
            
            if upload_response.status_code == 200:
                # Parse response
                try:
                    upload_data = upload_response.json()
                    
                    result = {
                        "success": True,
                        "operation": "jira_upload_attachment",
                        "ticket_number": ticket_number,
                        "file_path": file_path_expanded,
                        "file_name": file_name,
                        "file_size_bytes": file_size,
                        "file_size_kb": file_size_kb,
                        "jira_url": jira_url,
                        "attachments": []
                    }
                    
                    # Process uploaded attachments
                    if isinstance(upload_data, list):
                        for attachment in upload_data:
                            attachment_info = {
                                "id": attachment.get("id"),
                                "filename": attachment.get("filename"),
                                "size": attachment.get("size"),
                                "mime_type": attachment.get("mimeType"),
                                "author": attachment.get("author", {}).get("displayName"),
                                "created": attachment.get("created"),
                                "content_url": attachment.get("content")
                            }
                            result["attachments"].append(attachment_info)
                    
                    # Add comment if provided
                    if comment:
                        comment_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ticket_number}/comment"
                        comment_data = {"body": comment}
                        comment_headers = {
                            "Authorization": f"Bearer {jira_auth}",
                            "Content-Type": "application/json"
                        }
                        
                        try:
                            comment_response = requests.post(
                                comment_url,
                                headers=comment_headers,
                                json=comment_data,
                                timeout=30
                            )
                            
                            if comment_response.status_code == 201:
                                result["comment_added"] = True
                                result["comment"] = comment
                            else:
                                result["comment_added"] = False
                                result["comment_error"] = f"Failed to add comment: {comment_response.status_code}"
                                
                        except Exception as e:
                            result["comment_added"] = False
                            result["comment_error"] = f"Failed to add comment: {str(e)}"
                    
                    return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
                    
                except json.JSONDecodeError:
                    # Upload succeeded but response parsing failed
                    result = {
                        "success": True,
                        "operation": "jira_upload_attachment",
                        "ticket_number": ticket_number,
                        "file_path": file_path_expanded,
                        "file_name": file_name,
                        "file_size_bytes": file_size,
                        "file_size_kb": file_size_kb,
                        "message": "File uploaded successfully but response parsing failed",
                        "raw_response": upload_response.text[:1000]  # First 1000 chars
                    }
                    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                    
            elif upload_response.status_code == 401:
                error_result = {
                    "success": False,
                    "error": "Authentication failed. Check your API token.",
                    "status_code": 401
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            elif upload_response.status_code == 403:
                error_result = {
                    "success": False,
                    "error": "Permission denied. Check if you have permission to add attachments to this ticket.",
                    "status_code": 403
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            elif upload_response.status_code == 404:
                error_result = {
                    "success": False,
                    "error": f"Ticket {ticket_number} not found. Check the ticket number.",
                    "status_code": 404
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            elif upload_response.status_code == 413:
                error_result = {
                    "success": False,
                    "error": f"File too large ({file_size_kb} KB). Check Jira attachment size limits.",
                    "status_code": 413
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            else:
                error_result = {
                    "success": False,
                    "error": f"Upload failed with status {upload_response.status_code}",
                    "status_code": upload_response.status_code,
                    "response": upload_response.text[:1000]  # First 1000 chars
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
        except requests.exceptions.Timeout:
            error_result = {
                "success": False,
                "error": "Upload timeout. File may be too large or network connection is slow."
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
                "error": f"Upload failed: {str(e)}"
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
