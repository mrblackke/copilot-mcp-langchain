# JavaScript Function Management Tool (lng_javascript)

JavaScript function management and execution tool with full console.log support for debugging.

## Features

- **Function Storage**: Save JavaScript functions to filesystem for reuse
- **Function Execution**: Execute saved functions with parameters
- **Console Logging**: Full support for `console.log`, `console.warn`, and `console.error` with automatic log capture
- **Parameter Handling**: Support for JSON objects, strings, and complex data types
- **Modern JavaScript**: Full ES6+ support via PyMiniRacer engine

## Console Logging Support

JavaScript functions now support full console logging! All `console.log`, `console.warn`, and `console.error` calls are automatically captured and logged to both:
- **Server log files** (`mcp_server/logs/mcp_server.log`)
- **Original console** (print output)

### Log Format
```
JS Console: [JS LOG] Your log message
JS Console: [JS WARN] Your warning message  
JS Console: [JS ERROR] Your error message
```

### Example JavaScript Function with Logging
```javascript
function processData(params) {
    console.log('Processing data:', JSON.stringify(params));
    console.warn('This is a warning for debugging');
    
    if (!params.data) {
        console.error('Missing required data parameter');
        return { error: 'Missing data' };
    }
    
    console.log('Processing completed successfully');
    return { result: params.data.toUpperCase() };
}
```

**Calling with Object Parameters:**
```json
{
    "function_name": "processData",
    "parameters": {
        "data": "hello world",
        "options": {"format": "uppercase"},
        "metadata": {"timestamp": "2025-08-11"}
    }
}
```

When executed, all console messages will appear in the server logs with timestamps and proper formatting.

## Available Tools

This JavaScript management system provides three separate tools:

### 1. `lng_javascript_add` - Save JavaScript Functions
Save JavaScript functions to filesystem for later execution.

**Parameters:**
- `function_name` (string, required): Name of the function (must match function declaration)
- `function_code` (string, required): JavaScript function code (must be declared function, not arrow function)

**Example:**
```json
{
    "function_name": "calculateSum",
    "function_code": "function calculateSum(params) { console.log('Calculating:', params); return params.a + params.b; }"
}
```

### 2. `lng_javascript_execute` - Execute JavaScript Functions with Console Support
Execute previously saved JavaScript functions with parameters and full console.log debugging support.

**Parameters:**
- `function_name` (string, required): Name of the saved function to execute
- `parameters` (object, optional): Parameters to pass to the function

**Example with Object Parameters:**
```json
{
    "function_name": "calculateSum", 
    "parameters": {"a": 5, "b": 3}
}
```

**Example with Complex Data:**
```json
{
    "function_name": "processData", 
    "parameters": {
        "data": "hello world",
        "options": {"format": "uppercase"},
        "metadata": {"timestamp": "2025-08-11"}
    }
}
```

### 3. `lng_javascript_list` - List Saved Functions
Show all saved JavaScript functions.

**Example:**
```json
{}
```

## Function Requirements

- Must be **declared functions** (not arrow functions)
- Function name must match the `function_name` parameter
- Functions can contain any JavaScript code including async/await
- Functions are stored in `mcp_server/config/javascript/` directory with `.js` extension

**Parameter Handling in lng_javascript_execute:**

The `lng_javascript_execute` tool intelligently handles different parameter types with automatic conversion:

**Object Parameters (Recommended):**
```json
"parameters": {"name": "John", "age": 30, "items": [1, 2, 3]}
```
Objects are passed directly to JavaScript functions without conversion.

**JSON String Parameters:**
```json
"parameters": "{\"name\": \"John\", \"age\": 30, \"items\": [1, 2, 3]}"
```
JSON strings are automatically parsed into objects.

**Plain String Parameters:**
```json
"parameters": "Hello World"
```
Plain strings are passed as-is to JavaScript functions.

**Parameter Processing Order:**
1. **Objects/Arrays** → passed directly (no conversion)
2. **JSON strings** → parsed and passed as objects  
3. **Plain strings** → passed as strings
4. **Other types** → converted to strings

## Console Logging Examples

```javascript
// Basic logging
function exampleFunction(params) {
    console.log('Function started with:', params);
    console.warn('This is a warning message');
    console.error('This is an error message');
    
    // Object logging (automatically JSON.stringify)
    console.log('Complex object:', { 
        data: params, 
        timestamp: new Date().toISOString() 
    });
    
    return 'completed';
}
```

All console messages will be captured and appear in the server logs like this:
```
2025-08-11 23:45:33,011 - mcp_server.tools.lng_javascript.tool - INFO - JS Console: [JS LOG] Function started with: test_data
2025-08-11 23:45:33,011 - mcp_server.tools.lng_javascript.tool - INFO - JS Console: [JS WARN] This is a warning message
2025-08-11 23:45:33,011 - mcp_server.tools.lng_javascript.tool - INFO - JS Console: [JS ERROR] This is an error message
2025-08-11 23:45:33,011 - mcp_server.tools.lng_javascript.tool - INFO - JS Console: [JS LOG] Complex object: {"data":"test_data","timestamp":"2025-08-11T23:45:33.011Z"}
```

## Output

- **Success**: Returns actual function result (JSON or text)
- **Error**: JSON object with error message: `{"error": "error_description"}`
- **Logs**: All console messages captured automatically in server logs

## Technical Details

- **Engine**: PyMiniRacer for JavaScript execution
- **Storage**: File-based storage in `mcp_server/config/javascript/`
- **Logging**: Dual output (console + log file) with prefixed messages
- **Error Handling**: Comprehensive error capture and reporting
