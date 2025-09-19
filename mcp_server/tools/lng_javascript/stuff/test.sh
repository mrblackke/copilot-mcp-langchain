#!/bin/bash

####################################
### activate virtual environment ###
####################################
cd ../../../../
if [ -f "./.virtualenv/Scripts/activate" ]; then
    # Windows
    . ./.virtualenv/Scripts/activate
elif [ -f "./.virtualenv/bin/activate" ]; then
    # Linux/Unix
    . ./.virtualenv/bin/activate
else
    echo "Virtual environment not found!"
    exit 1
fi

##############################
### lng_javascript_list    ###
### lng_javascript_add     ###
### lng_javascript_execute ###
##############################
# Testing JavaScript function management and execution

echo "🚀 lng_javascript separate tools testing - comprehensive coverage"
echo

# Test 1: List functions when none exist using lng_javascript_list
echo "📋 TEST 1: List functions when none exist (lng_javascript_list)"
python -m mcp_server.run run lng_javascript_list '{}'
echo

# Test 2: Add a simple greeting function with console logging using lng_javascript_add
echo "📋 TEST 2: Add simple greeting function with console logging (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "greet", "function_code": "function greet(params) { console.log(\"Greeting called with:\", params); return \"Hello, \" + params; }"}'
echo

# Test 3: Execute greeting function with string parameter using lng_javascript_execute
echo "📋 TEST 3: Execute greeting function with string parameter (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "greet", "parameters": "World"}'
echo

# Test 4: Add function with comprehensive console logging using lng_javascript_add
echo "📋 TEST 4: Add function with comprehensive console logging (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "calculateSum", "function_code": "function calculateSum(params) { console.log(\"Starting calculation:\", params); if (!params.a || !params.b) { console.warn(\"Missing parameters - using defaults\"); params.a = params.a || 0; params.b = params.b || 0; } const result = params.a + params.b; if (result < 0) { console.error(\"Negative result detected:\", result); } console.log(\"Calculation completed:\", result); return result; }"}'
echo

# Test 5: Execute function with object parameters using lng_javascript_execute
echo "📋 TEST 5: Execute function with object parameters (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "calculateSum", "parameters": {"a": 5, "b": 3}}'
echo

# Test 6: Add debug function with all console types using lng_javascript_add
echo "📋 TEST 6: Add debug function with all console types (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "debugExample", "function_code": "function debugExample(params) { console.log(\"=== Debug function started ===\"); console.log(\"Parameters received:\", JSON.stringify(params, null, 2)); if (params.debug) { console.warn(\"Debug mode enabled - showing detailed info\"); console.log(\"Parameter keys:\", Object.keys(params)); } if (params.simulate_error) { console.error(\"Simulated error condition!\"); } const result = { input: params, timestamp: new Date().toISOString(), processed: true }; console.log(\"Final result:\", JSON.stringify(result, null, 2)); return result; }"}'
echo

# Test 7: Execute debug function with complex object parameters using lng_javascript_execute
echo "📋 TEST 7: Execute debug function with complex object (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "debugExample", "parameters": {"debug": true, "user": {"name": "TestUser", "age": 30}, "options": {"verbose": true}, "simulate_error": true}}'
echo

# Test 8: Add modern JavaScript function using lng_javascript_add
echo "📋 TEST 8: Add modern JavaScript function (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "processArray", "function_code": "function processArray(params) { console.log(\"Processing array:\", params); const { numbers, operation } = params; console.log(\"Operation:\", operation, \"Numbers:\", numbers); if (operation === \"sum\") { const result = numbers.reduce((a, b) => a + b, 0); console.log(\"Sum result:\", result); return result; } if (operation === \"average\") { const sum = numbers.reduce((a, b) => a + b, 0); const avg = sum / numbers.length; console.log(\"Average result:\", avg); return avg; } console.warn(\"Unknown operation:\", operation); return \"Unknown operation\"; }"}'
echo

# Test 9: Execute modern function with array sum using lng_javascript_execute
echo "📋 TEST 9: Execute modern function - array sum (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "processArray", "parameters": {"numbers": [1, 2, 3, 4, 5], "operation": "sum"}}'
echo

# Test 10: Execute modern function with array average using lng_javascript_execute
echo "📋 TEST 10: Execute modern function - array average (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "processArray", "parameters": {"numbers": [10, 20, 30], "operation": "average"}}'
echo

# Test 11: List all saved functions using lng_javascript_list
echo "📋 TEST 11: List all saved functions (lng_javascript_list)"
python -m mcp_server.run run lng_javascript_list '{}'
echo

# Test 12: Error handling - execute nonexistent function using lng_javascript_execute
echo "📋 TEST 12: Error handling - execute nonexistent function (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "nonexistent", "parameters": "test"}'
echo

# Test 13: Error handling - invalid function name using lng_javascript_add
echo "📋 TEST 13: Error handling - function name mismatch (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "wrongName", "function_code": "function correctName(params) { return params; }"}'
echo

# Test 14: Add complex function with comprehensive logging using lng_javascript_add
echo "📋 TEST 14: Add complex function with comprehensive logging (lng_javascript_add)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "complexCalc", "function_code": "function complexCalc(params) { console.log(\"Complex calculation started:\", params); const { operation, value1, value2 } = params; console.log(\"Operation:\", operation, \"Value1:\", value1, \"Value2:\", value2); let result; switch(operation) { case \"multiply\": result = value1 * value2; console.log(\"Multiplication result:\", result); break; case \"divide\": if (value2 === 0) { console.error(\"Division by zero attempted!\"); result = \"Division by zero\"; } else { result = value1 / value2; console.log(\"Division result:\", result); } break; case \"power\": result = Math.pow(value1, value2); console.log(\"Power result:\", result); break; default: console.warn(\"Unknown operation:\", operation); result = \"Unknown operation\"; } return result; }"}'
echo

# Test 15: Execute complex function - multiplication using lng_javascript_execute
echo "📋 TEST 15: Execute complex function - multiplication (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "complexCalc", "parameters": {"operation": "multiply", "value1": 7, "value2": 6}}'
echo

# Test 16: Execute complex function - power using lng_javascript_execute
echo "📋 TEST 16: Execute complex function - power (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "complexCalc", "parameters": {"operation": "power", "value1": 2, "value2": 8}}'
echo

# Test 17: Execute complex function - division by zero using lng_javascript_execute
echo "📋 TEST 17: Execute complex function - division by zero (lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_execute '{"function_name": "complexCalc", "parameters": {"operation": "divide", "value1": 10, "value2": 0}}'
echo

# Test 18: Batch execution - create and execute function using lng_batch_run
echo "📋 TEST 18: Batch execution - create and execute function (lng_batch_run)"
python -m mcp_server.run run lng_batch_run '{"pipeline": [{"tool": "lng_javascript_add", "params": {"function_name": "batchTest", "function_code": "function batchTest(params) { console.log(\"Batch function called:\", params); return \"Batch result: \" + JSON.stringify(params); }"}, "output": "add_result"}, {"tool": "lng_javascript_execute", "params": {"function_name": "batchTest", "parameters": {"message": "batch execution test", "success": true}}, "output": "exec_result"}], "final_result": "{! exec_result !}"}'
echo

# Test 19: String manipulation with extensive logging using lng_javascript_add and lng_javascript_execute
echo "📋 TEST 19: String manipulation with extensive logging (lng_javascript_add + lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "processText", "function_code": "function processText(params) { console.log(\"Text processing started:\", params); const text = params.text || \"\"; console.log(\"Original text:\", text); const result = { original: text, uppercase: text.toUpperCase(), lowercase: text.toLowerCase(), length: text.length, words: text.split(\" \").filter(w => w.length > 0).length, reversed: text.split(\"\").reverse().join(\"\") }; console.log(\"Processing results:\", JSON.stringify(result, null, 2)); return result; }"}'
python -m mcp_server.run run lng_javascript_execute '{"function_name": "processText", "parameters": {"text": "Hello JavaScript World with Console Logging!"}}'
echo

# Test 20: Date and time operations with logging using lng_javascript_add and lng_javascript_execute
echo "📋 TEST 20: Date operations with logging (lng_javascript_add + lng_javascript_execute)"
python -m mcp_server.run run lng_javascript_add '{"function_name": "dateOperations", "function_code": "function dateOperations(params) { console.log(\"Date operations called:\", params); const now = new Date(); console.log(\"Current timestamp:\", now.getTime()); const dayNames = [\"Sunday\", \"Monday\", \"Tuesday\", \"Wednesday\", \"Thursday\", \"Friday\", \"Saturday\"]; const monthNames = [\"January\", \"February\", \"March\", \"April\", \"May\", \"June\", \"July\", \"August\", \"September\", \"October\", \"November\", \"December\"]; const result = { timestamp: now.getTime(), dayOfWeek: dayNames[now.getDay()], month: monthNames[now.getMonth()], formatted: now.toISOString(), year: now.getFullYear(), readable: now.toLocaleDateString() + \" \" + now.toLocaleTimeString() }; console.log(\"Date operation results:\", JSON.stringify(result, null, 2)); return result; }"}'
python -m mcp_server.run run lng_javascript_execute '{"function_name": "dateOperations", "parameters": {}}'
echo

echo "🎉 lng_javascript separate tools testing completed!"
echo "All JavaScript function management features tested with console.log support!"
echo "Check server logs for detailed console output from JavaScript functions."