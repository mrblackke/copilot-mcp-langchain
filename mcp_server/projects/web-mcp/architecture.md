# Web MCP Interface Architecture

## Project Goal
Create a Swagger-like web interface for existing MCP tool- **Logging**: Tool execution logged on server side (not exposed in UI)

## Deployment Options
- **Local Development**: `bind_host: "localhost"` or `bind_host: "127.0.0.1"`
- **Network Access**: `bind_host: "0.0.0.0"` to allow access from other machines
- **Port Configuration**: Configurable port (default: 8080)
- **URL Examples**:
  - Local: `http://localhost:8080`
  - Network: `http://your-ip-address:8080`

## Target Usersallowing users to interact with tools through a browser without using an IDE.

Currently, MCP tools have 3 access methods:
1. **Terminal** - Direct command-line usage
2. **MCP Protocol** - Through MCP-enabled IDEs and clients
3. **Pipeline** - Via `lng_batch_run` tool

This project adds a **4th access method**: **Web Interface** for universal browser-based access.

## Architecture

**Foundation**: `lng_webhook_server` with static file support and API endpoints

**Project Structure**:
```
mcp_server/projects/web-mcp/
├── config/
│   └── webhook_config.json     # lng_webhook_server configuration
├── static/
│   └── index.html             # Single page application (HTML+JS+CSS)
├── readme.md                  # Launch instructions
└── run.ps1                    # Quick start script for PowerShell
```

## Technical Implementation

### Backend (lng_webhook_server)
- **Static Files**: Serve `index.html` from `/static/` directory via HTML routes
- **API Endpoints**:
  - `/api/tools` - Returns schemas of all available tools
  - `/api/execute` - Universal endpoint for tool execution
- **HTML Routes Configuration**: Use `html_routes` feature in webhook config
- **Local & Network Access**: Support both localhost and network binding (0.0.0.0)

### Universal Tool Execution
**Endpoint**: `POST /api/execute`
**Request**: `{"tool": "tool_name", "params": {...}}`
**Pipeline Implementation**: 
```json
{
  "pipeline": [
    {
      "tool": "{! webhook.body.tool !}",
      "params": "{! webhook.body.params !}",
      "output": "result"
    }
  ]
}
```
**Dynamic Tool Routing**: Uses `{! !}` expressions to dynamically route tool calls based on request payload

### Tool Discovery
- Use `tool_registry.py` to get list of enabled tools via `get_available_tools()` function
- Filter tools based on `settings.yaml` configuration (exclude disabled tools)
- Extract schemas from each tool's `tool_info()` function
- Use `lng_get_tools_info` tool to retrieve comprehensive tool information
- Group tools by directory structure (e.g., `lng_file`, `lng_http_client`, `lng_jira`)
- Only show tools that are not disabled in configuration
- **Dynamic Loading**: Tools list refreshed on each page load to reflect current configuration

## Frontend Features

### Core Functionality
- ✅ **Tool Listing**: Display all available tools with descriptions
- ✅ **Dynamic Forms**: Auto-generate forms based on tool schemas
- ✅ **Tool Execution**: Call tools via web forms
- ✅ **Documentation**: Show tool descriptions and parameter details

### User Interface
- **Technology Stack**: Vanilla HTML/JavaScript/CSS (no frameworks)
- **Single Page**: Everything embedded in `index.html`
- **Responsive Design**: Works on desktop and mobile
- **Dynamic Generation**: JavaScript dynamically constructs all UI elements, forms, and tool lists based on available tools

### Tool Organization
- **Grouping**: Group tools by folder structure (e.g., `lng_file/*`, `lng_http_client/*`)
- **Display**: Show all tools on main screen with hashtag-style group filters
- **Search**: Combined search across tool names, descriptions, and schemas
- **Filtering**: 
  - Click hashtags to filter by group (e.g., `#file`, `#http`, `#jira`)
  - Real-time search as you type
  - Clear filters to show all tools
- **Categories**: Auto-generated from tool directory names

### Form Generation
- **Parameter Support**: All JSON Schema types (strings, numbers, arrays, objects)
- **Complex Parameters**: Handle `enum`, `oneOf`, conditional fields based on MCP schemas
- **Validation**: Client-side validation with **force-disable option** to bypass validation
- **Schema-Driven**: Forms auto-generated from MCP tool schemas
- **Real-time**: Form validation and feedback as user types
- **Dynamic Construction**: JavaScript dynamically builds all forms based on available tools and their schemas

### Results Display
- **JSON**: Syntax highlighting for JSON responses
- **Text**: Plain text display for non-JSON responses
- **Smart Detection**: Auto-detect JSON vs plain text content
- **Actions**: 
  - Copy to clipboard functionality (primary action) - single click copy
  - Download as file (secondary action)
- **Formatting**: Pretty-print JSON with collapsible sections

### User Experience
- **No History**: No localStorage persistence (history available in server logs)
- **No Bookmarks**: Simple, stateless interface
- **No Form Persistence**: Forms reset on reload
- **Real-time**: Immediate tool execution and results
- **Logging**: Tool execution logged on server side (not exposed in UI)

## Target Users
- **Developers**: Testing and debugging MCP tools
- **End Users**: Accessing tools without IDE setup
- **System Administrators**: Managing and monitoring tools
- **Anyone**: Universal browser-based access without technical barriers

## Security & Access
- **No Authentication**: Open access (for now)
- **No Restrictions**: All enabled tools available
- **Tool Filtering**: Based on `settings.yaml` and `tool_registry.py`

## Startup Process
1. Run `run.ps1` script (PowerShell)
2. Script activates virtual environment
3. Script launches `lng_webhook_server` with config from `config/webhook_config.json`
4. Server starts on configured host/port (supports both localhost and network access)
5. Web interface available at configured URL
6. Tools dynamically loaded via `/api/tools` endpoint on page load

## Data Flow
1. **Page Load**: Fetch tool schemas from `/api/tools`
2. **UI Generation**: Build tool list and forms dynamically
3. **Tool Execution**: POST to `/api/execute` with tool name and parameters
4. **Results Display**: Show formatted response with copy/download options

## Configuration Examples

### Webhook Server Configuration (`config/webhook_config.json`)
```json
{
  "name": "web-mcp-interface",
  "port": 8080,
  "bind_host": "0.0.0.0",
  "html_routes": [
    {
      "pattern": "/",
      "template": "mcp_server/projects/web-mcp/static/index.html",
      "mapping": {
        "TITLE": "MCP Tools Web Interface",
        "VERSION": "1.0.0",
        "BASE_URL": "http://localhost:8080"
      }
    }
  ],
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body": {"status": "MCP Web Interface API"}
  },
  "pipeline": [
    {
      "type": "condition",
      "condition": "{! webhook.path === '/api/tools' !}",
      "then": [
        {
          "tool": "lng_get_tools_info",
          "params": {},
          "output": "tools_info"
        }
      ],
      "else": [
        {
          "type": "condition", 
          "condition": "{! webhook.path === '/api/execute' && webhook.method === 'POST' !}",
          "then": [
            {
              "tool": "{! webhook.body.tool !}",
              "params": "{! webhook.body.params || {} !}",
              "output": "execution_result"
            }
          ]
        }
      ]
    }
  ]
}
```

## Technical Requirements

### Expression System
- Utilize `lng_batch_run` expression capabilities
- Support `{! !}` JavaScript expressions for dynamic tool routing
- Enable flexible parameter passing

### Error Handling
- Display clear error messages for failed tool executions
- Show validation errors for form inputs
- Handle network and server errors gracefully
- Provide fallback UI for when API is unavailable

### Performance
- Minimal JavaScript footprint
- Fast tool schema loading
- Responsive form generation
- Efficient DOM manipulation

### Browser Compatibility
- Modern browsers with ES6+ support
- No external JavaScript dependencies
- Vanilla CSS without preprocessors
- Progressive enhancement approach

## Dependencies
- **Backend**: `lng_webhook_server`, `lng_batch_run`, existing MCP tool infrastructure
- **Frontend**: No external dependencies (vanilla HTML/JS/CSS)
- **Runtime**: Python MCP server with activated virtual environment

## Implementation Details

### JavaScript Architecture
- **Module Pattern**: Self-contained JavaScript modules
- **Event-Driven**: DOM events and AJAX callbacks
- **State Management**: Simple object-based state without frameworks
- **Form Generation**: Dynamic HTML generation based on JSON schemas

### CSS Styling
- **Responsive Design**: Mobile-first CSS Grid and Flexbox
- **Component-Based**: Reusable CSS classes for UI components
- **Theme Support**: CSS custom properties for easy theming
- **No Framework**: Pure CSS without Bootstrap or similar

### API Integration  
- **Fetch API**: Modern promise-based HTTP requests
- **Error Handling**: Comprehensive try-catch with user feedback
- **Request Validation**: Client-side validation before server calls
- **Response Processing**: Smart content-type detection and formatting
