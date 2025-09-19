## Info
- This case demonstrates a simple webhook calculator that accepts mathematical expressions and returns calculation results via REST API

## How to ask for demo in chat  
Use this case to make demo:
```
Show me demo from file:
Create a simple calculator webhook that accepts math expressions via GET/POST requests and returns JSON results.
```

## 🤖 AI Instructions
1. List webhooks → stop `calculator-webhook` if exists
2. Create: `lng_webhook_server` → port 8089, path `/calculate`, pipeline with `lng_math_calculator`
3. Test: GET `?expression=2%2B3*4` → `14`, POST `{"expression":"sqrt(16)+2^3"}` → `12`

**Key**: Use `{! webhook.body.expression || webhook.query.expression !}` for input, encode `+` as `%2B` in GET

## Important
- Webhook runs on port 8089 at http://localhost:8089/calculate
- Supports both GET query parameters and POST body
- ⚠️ Important: In GET requests, the `+` symbol must be encoded as `%2B`
- Uses MCP tool lng_math_calculator for calculations

## Scenario
Webhook `/calculate` that:
- Accepts mathematical expressions via `expression` parameter
- Calculates result using `lng_math_calculator`
- Returns JSON response with result, expression and timestamp

## API Usage Examples

### GET Request (important: + symbol must be encoded as %2B)
```
http://localhost:8089/calculate?expression=2%2B3*4
http://localhost:8089/calculate?expression=sqrt(25)%2B10
http://localhost:8089/calculate?expression=pi*2%5E2
```

### POST Request
```
POST http://localhost:8089/calculate
Content-Type: application/json

{
  "expression": "sqrt(16) + 2^3"
}
```

### PowerShell Examples
```powershell
# GET request
Invoke-WebRequest -Uri "http://localhost:8089/calculate?expression=2%2B3*4"

# POST request
Invoke-WebRequest -Uri "http://localhost:8089/calculate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"expression": "pi * 2^2"}'
```

## Response Format
```json
{
  "endpoint": "Math Calculator API",
  "success": true,
  "expression": "2+3*4", 
  "method": "GET",
  "result": 14,
  "result_type": "int",
  "error": null,
  "timestamp": "2025-08-19T13:50:00.123456"
}
```

## Supported Operations
- Basic arithmetic: +, -, *, /
- Power: ** or ^
- Functions: sqrt, sin, cos, tan, log, ln, abs
- Constants: pi, e
- Parentheses for grouping

## Testing
The webhook can be tested via:
- Browser for GET requests
- Postman/curl for POST requests  
- MCP test function for automated testing