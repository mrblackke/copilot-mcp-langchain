## Info
- This case demonstrates an HTML calculator webpage that displays mathematical expressions and calculation results in a beautiful web interface

## How to ask for demo in chat  
Use this case to make demo:
```
Show me demo from file:
I need calculator HTML webpage that shows calculation results with expression and statistics in a nice web interface.
```

## 🤖 AI Instructions
1. List webhooks → stop `calculator-html` if exists
2. Use HTML template file `./calculator-result.html`
3. Create 
  + `lng_webhook_server` → port 8090 pipeline 
  + with `calculator-html` name
  + with path `/calc` 
  + with `lng_math_calculator` inside pipeline 
  + and HTML response with template. Use `html_routes` with `pattern`, `template` and `mapping`.
4. Test: GET `?expression=2%2B3*4` → HTML page with result, POST `{"expression":"sqrt(16)+2^3"}` → HTML page

**Key**: Use `{! webhook.body.expression || webhook.query.expression !}` for input, return HTML with calculation details

## Important
- Webhook runs on port 8090 at http://localhost:8090/calc
- Returns HTML page instead of JSON
- ⚠️ Important: In GET requests, the `+` symbol must be encoded as `%2B`
- Uses MCP tool lng_math_calculator for calculations
- Shows expression, result, and additional statistics

## Scenario
Webhook `/calc` that:
- Accepts mathematical expressions via `expression` parameter
- Calculates result using `lng_math_calculator`
- Returns beautiful HTML page with result, expression, timestamp, and calculation details

## API Usage Examples

### GET Request (important: + symbol must be encoded as %2B)
```
http://localhost:8090/calc?expression=2%2B3*4
http://localhost:8090/calc?expression=sqrt(25)%2B10
http://localhost:8090/calc?expression=pi*2%5E2
```

### POST Request
```
POST http://localhost:8090/calc
Content-Type: application/json

{
  "expression": "sqrt(16) + 2^3"
}
```

### PowerShell Examples
```powershell
# GET request
Start-Process "http://localhost:8090/calc?expression=2%2B3*4"

# POST request (will show HTML in browser)
Invoke-WebRequest -Uri "http://localhost:8090/calc" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"expression": "pi * 2^2"}'
```

## HTML Response Features
- Beautiful responsive design similar to cookie status page
- Expression input display
- Calculation result with type
- Timestamp and method information
- Error handling with friendly messages
- Mathematical symbols and formatting

## Template Variables
- `{{EXPRESSION}}` - The mathematical expression
- `{{RESULT}}` - Calculation result
- `{{RESULT_TYPE}}` - Type of result (int, float, complex)
- `{{METHOD}}` - HTTP method used
- `{{TIMESTAMP}}` - Current timestamp
- `{{ERROR}}` - Error message if any
- `{{SUCCESS}}` - Success status

## Supported Operations
- Basic arithmetic: +, -, *, /
- Power: ** or ^
- Functions: sqrt, sin, cos, tan, log, ln, abs
- Constants: pi, e
- Parentheses for grouping

## Testing
The webhook can be tested via:
- Browser for GET requests (shows HTML page)
- Postman/curl for POST requests
- Direct URL access for quick calculations