import mcp.types as types
import os
import json
import requests
from pathlib import Path

async def tool_info() -> dict:
    """Returns information about the lng_jira_get_description tool."""
    return {
        "description": """Retrieves detailed information from a Jira ticket including description, metadata, and status.

**Parameters:**
- `ticket_number` (string, required): Jira ticket number (e.g., "PROJ-123")
- `output_file` (string, optional): Path to save the JSON output file
- `env_file` (string, optional): Path to .env file (default: ".env")

**Environment Variables Required:**
- `JIRA_URL`: Base URL of your Jira instance (e.g., "https://yourcompany.atlassian.net")
- `JIRA_AUTH`: Bearer token for Jira API authentication

**Returns:**
- Complete ticket information including:
  - Summary, description, status, assignee, reporter
  - Created/updated dates, priority, issue type
  - JSON formatted response with all field details

**Example Usage:**
- Get ticket info: `{"ticket_number": "PROJ-123"}`
- Save to file: `{"ticket_number": "PROJ-123", "output_file": "ticket_data.json"}`

**Error Handling:**
- Validates environment variables and authentication
- Handles missing tickets and permission errors
- Returns detailed error messages for troubleshooting""",
        "schema": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "Jira ticket number (e.g., PROJ-123)"
                },
                "output_file": {
                    "type": "string",
                    "description": "Optional: Path to save the JSON output file"
                },
                "env_file": {
                    "type": "string",
                    "description": "Optional: Path to .env file (default: .env)"
                }
            },
            "required": ["ticket_number"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Retrieves detailed information from a Jira ticket."""
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
        output_file = parameters.get("output_file")
        env_file = parameters.get("env_file", ".env")
        
        if not ticket_number:
            error_result = {
                "success": False,
                "error": "ticket_number parameter is required"
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
        
        # Prepare API request
        api_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ticket_number}"
        fields = "summary,description,status,assignee,reporter,created,updated,priority,issuetype"
        full_url = f"{api_url}?fields={fields}"
        
        headers = {
            "Authorization": f"Bearer {jira_auth}",
            "Accept": "application/json"
        }
        
        try:
            # Make API request
            response = requests.get(full_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                ticket_data = response.json()
                
                # Save to file if requested
                if output_file:
                    output_path = os.path.expanduser(output_file)
                    if not os.path.isabs(output_path):
                        output_path = os.path.abspath(output_path)
                    
                    try:
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(ticket_data, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        # Still return data even if file save fails
                        error_note = f"Warning: Failed to save to file {output_path}: {str(e)}"
                        ticket_data["_file_save_error"] = error_note
                
                # Prepare result
                result = {
                    "success": True,
                    "operation": "jira_get_description",
                    "ticket_number": ticket_number,
                    "jira_url": jira_url,
                    "data": ticket_data
                }
                
                if output_file:
                    result["output_file"] = output_file
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
                
            elif response.status_code == 401:
                error_result = {
                    "success": False,
                    "error": "Authentication failed. Check your API token.",
                    "status_code": 401
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            elif response.status_code == 403:
                error_result = {
                    "success": False,
                    "error": "Permission denied. Check if you have access to this ticket.",
                    "status_code": 403
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            elif response.status_code == 404:
                error_result = {
                    "success": False,
                    "error": f"Ticket {ticket_number} not found. Check the ticket number.",
                    "status_code": 404
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
            else:
                error_result = {
                    "success": False,
                    "error": f"API request failed with status {response.status_code}",
                    "status_code": response.status_code,
                    "response": response.text[:1000]  # First 1000 chars of response
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
                
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
