## Info
- This case demonstrates the complete corporate-grade encrypted cookies grabbing workflow with browser-side AES-256-GCM encryption, secure storage, and HTTP client integration for protected API access.

## How to ask for demo in chat  
Use this case to make demo:
```
Show me demo from file:
I need to make secure call to the `https://next.telescope.epam.com/apps/menu/api/users/me`
```

## 🤖 AI Instructions

#### 1. Start `lng_cookies_grabber` tool
1. Start the grabber:
```json
{
  "operation": "start"
}
```

#### 2. Access the Status Page
Show to the user. Open `http://localhost:9000/cookies/YOUR_SESSION_ID` in your browser. Please choose any id you want here insted of `YOUR_SESSION_ID`. Make this link clickable. 

#### 3. Install Chrome Extension
Ask user to follow this instructions:
1. Download `background.js` and `manifest.json` from the status page
2. Create a new folder and place both files inside
3. Open Chrome Extensions (`chrome://extensions/`)
4. Enable Developer Mode
5. Click `Load unpacked` and select your folder

#### 4. Grab the Cookies
Ask user to follow this instructions:
1. Click the `🚀 Run Encrypted Cookie Grabber`  button on the status page
2. The extension will automatically visit all configured portals and cookies will be collected
3. Then enter `master password` in the popup to encode your cookies and make this more secure.
4. Cookies will be stored securely in folder `mcp_server/config/cookies/YOUR_SESSION_ID/all_domains.encrypted`

#### 5. Wait for user
1. Please stop and wait till user doing `#### 3.` and `#### 4.`
2. When user is ready, continue with following.

#### 6. Use the System
1. You can check all session with `lng_cookies_grabber` tool
```json
{
  "operation": "list_sessions"
}
```
2. Then just use the `lng_http_server` tool to access the restricted Rest API. 
3. For example, this will get page without cookies. Show this to user.
```json
{
  "mode": "request",
  "url": "https://next.telescope.epam.com/apps/menu/api/users/me",
  "method": "GET"
}
```
4. And this will get page with cookies. Show this to user.
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
5. Make some conclusions about the differences between the two requests and how the cookies affect the response.