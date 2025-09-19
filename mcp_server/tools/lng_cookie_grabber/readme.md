## Cookie Grabber Tool

This tool provides a complete system for collecting cookies from multiple websites using a Chrome extension and WebSocket communication.

### System Components

1. **HTTP Webhook Server** - Serves HTML status page and extension files
2. **WebSocket Server** - Real-time communication with browser plugin
3. **Chrome Extension** - Collects cookies from specified portals

### Quick Start

#### 1. Start `lng_cookies_grabber` tool
By running tool will start 2 services.
```json
{
  "operation": "start"
}
```
1. This will share plugin scripts and status page:
```json
{
  "config_file": "mcp_server/tools/lng_cookie_grabber/webhook.json",
  "name": "cookie-status-custom",
  "operation": "start",
  "thread_mode": true
}
```
2. And this will start the WebSocket server that make bidirectional communication with the browser plugin to send cookie data:
```json
{
  "config_file": "mcp_server/tools/lng_cookie_grabber/websocket.json",
  "name": "cookie-websocket-custom", 
  "operation": "server_start"
}
```

#### 2. Access the Status Page
Open `http://localhost:9000/cookies/YOUR_SESSION_ID` in your browser

#### 3. Install Chrome Extension
1. Download `background.js` and `manifest.json` from the status page
2. Create a new folder and place both files inside
3. Open Chrome Extensions (`chrome://extensions/`)
4. Enable Developer Mode
5. Click `Load unpacked` and select your folder

#### 4. Grab the Cookies
1. Click the `🚀 Run Encrypted Cookie Grabber`  button on the status page
2. The extension will automatically visit all configured portals and cookies will be collected
3. Then enter `master password` in the popup to encode your cookies and make this more secure.
4. Cookies will be stored securely in folder `mcp_server/config/cookies/YOUR_SESSION_ID/all_domains.encrypted`

#### 5. Use the System
1. You can check all session with `lng_cookies_grabber` tool
```json
{
  "operation": "list_sessions"
}
```
2. Or just use the `lng_http_server` tool to access the restricted Rest API.
For example, this will get page without cookies:
```json
{
  "mode": "request",
  "url": "https://next.telescope.epam.com/apps/menu/api/users/me",
  "method": "GET"
}
And this will get page with cookies:
```json
{
  "mode": "request",
  "url": "https://next.telescope.epam.com/apps/menu/api/users/me",
  "method": "GET"
  "use_encrypted_cookies": {
    "auto_detect_domain": true,
    "domain": "next.telescope.epam.com",
    "session": "YOUR_SESSION_ID"
  }
}
```

### Configuration

- **HTTP Server Port**: 9000 (webhook.json)  
- **WebSocket Port**: 9001 (websocket.json)
- **Portals**: Configure in the `PORTALS` array in `webhook.json` or replace in `status.html`

### Logs

- `mcp_server/webhooks/cookie-status-server_*.log` - logs about http server that shares status page and plugin scripts
- `mcp_server/webhooks/cookie-websocket-server_*.log` - logs about websocket server that handles cookie data
- `mcp_server/mcp_server.log`- all logs