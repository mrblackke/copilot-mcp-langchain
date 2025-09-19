#!/usr/bin/env python3
"""
Universal test script for lng_javascript separate tools testing
Tests lng_javascript_add, lng_javascript_execute, and lng_javascript_list with given-when-then structure.
"""
import asyncio
import json
import sys
import logging
import os
from typing import Dict, Any, Optional

# Add the project root to sys.path so we can import from mcp_server
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
sys.path.insert(0, project_root)

# Change working directory to project root to ensure proper file paths
original_cwd = os.getcwd()
os.chdir(project_root)

from mcp_server.tools.tool_registry import initialize_tools, run_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('javascript_separate_tools_test')

class JavaScriptSeparateToolsTester:
    """Universal JavaScript testing utility for separate tools with given-when-then structure."""
    
    def __init__(self):
        self.test_results = []
        self.saved_functions = []
    
    async def cleanup_functions(self):
        """Clean up all functions created during testing."""
        logger.info(f"🧹 Cleaning up test functions...")
        
        # List all functions first using lng_javascript_list
        try:
            result = await run_tool("lng_javascript_list", {})
            function_list = json.loads(result[0].text)
            
            if function_list.get('functions'):
                logger.info(f"Found {len(function_list['functions'])} functions to clean up")
                # Note: We cannot delete functions individually with current implementation
                # Functions are managed by file_state_manager and persist across tests
                # This is intentional behavior for the tool
            else:
                logger.info("No functions found to clean up")
                
        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")
    
    def assert_result(self, test_name: str, expected: Any, actual: Any) -> bool:
        """Single assertion per test as requested."""
        success = expected == actual
        status = "✅ PASS" if success else "❌ FAIL"
        
        logger.info(f"{status} {test_name}")
        if not success:
            logger.info(f"  Expected: {expected}")
            logger.info(f"  Actual:   {actual}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "expected": expected,
            "actual": actual
        })
        
        return success
    
    async def run_javascript_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper function to run JavaScript tools and parse results."""
        try:
            result = await run_tool(tool_name, params)
            return json.loads(result[0].text)
        except json.JSONDecodeError as e:
            # If result is not JSON, return as plain text response
            return {"text_response": result[0].text}
        except Exception as e:
            return {"error": str(e)}
    
    # Test 1: List functions when none exist using lng_javascript_list
    async def test_list_empty_functions(self):
        """
        GIVEN: No JavaScript functions have been saved
        WHEN: I call lng_javascript_list
        THEN: I should get an empty functions list
        """
        # Given: Fresh state (handled by test setup)
        
        # When: List functions using dedicated tool
        result = await self.run_javascript_tool("lng_javascript_list", {})
        
        # Then: Should get empty list
        expected = {
            "message": "No JavaScript functions saved",
            "functions": []
        }
        
        # Compare only the relevant fields
        actual = {
            "message": result.get("message"),
            "functions": result.get("functions")
        }
        
        self.assert_result("List empty functions (lng_javascript_list)", expected, actual)
    
    # Test 2: Add a simple function using lng_javascript_add
    async def test_add_simple_function(self):
        """
        GIVEN: No function named 'greet' exists
        WHEN: I add a simple greeting function using lng_javascript_add
        THEN: I should get a success message with function details
        """
        # Given: No function exists (implicit)
        
        # When: Add simple function with console logging
        function_code = 'function greet(params) { console.log("Greeting called with:", params); return "Hello, " + params; }'
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "greet",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'greet' saved successfully",
            "function_name": "greet",
            "storage_path": "mcp_server/config/javascript/greet.js"
        }
        
        self.assert_result("Add simple function (lng_javascript_add)", expected, result)
        self.saved_functions.append("greet")
    
    # Test 3: Execute simple function with string parameter using lng_javascript_execute
    async def test_execute_function_string_param(self):
        """
        GIVEN: A 'greet' function has been saved
        WHEN: I execute it with a string parameter using lng_javascript_execute
        THEN: I should get the greeting result and see console logs
        """
        # Given: greet function exists (from previous test)
        
        # When: Execute with string parameter using dedicated execution tool
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "greet",
            "parameters": "World"
        })
        
        # Then: Should get greeting result
        expected = "Hello, World"
        actual = result.get("text_response", result)
        
        self.assert_result("Execute function with string param (lng_javascript_execute)", expected, actual)
    
    # Test 4: Add complex function with object parameters and console logging
    async def test_add_complex_function_with_logging(self):
        """
        GIVEN: I want to create a function with comprehensive console logging
        WHEN: I add a function using lng_javascript_add with console.log, console.warn, console.error
        THEN: I should get success confirmation
        """
        # Given: Want to add function with comprehensive logging
        
        # When: Add complex function with all console logging types
        function_code = '''function calculateSum(params) { 
            console.log("Starting calculation with params:", JSON.stringify(params)); 
            if (!params.a || !params.b) {
                console.warn("Missing parameters - using defaults");
                params.a = params.a || 0;
                params.b = params.b || 0;
            }
            const result = params.a + params.b; 
            if (result < 0) {
                console.error("Negative result detected:", result);
            }
            console.log("Calculation completed, result:", result);
            return result;
        }'''
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "calculateSum",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'calculateSum' saved successfully",
            "function_name": "calculateSum",
            "storage_path": "mcp_server/config/javascript/calculateSum.js"
        }
        
        self.assert_result("Add complex function with logging (lng_javascript_add)", expected, result)
        self.saved_functions.append("calculateSum")
    
    # Test 5: Execute function with object parameters using lng_javascript_execute
    async def test_execute_function_object_param(self):
        """
        GIVEN: A 'calculateSum' function has been saved
        WHEN: I execute it with object parameters using lng_javascript_execute
        THEN: I should get the calculated sum and see all console logs
        """
        # Given: calculateSum function exists
        
        # When: Execute with object parameters (new preferred approach)
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "calculateSum",
            "parameters": {"a": 5, "b": 3}
        })
        
        # Then: Should get sum result
        expected = 8
        # Handle both string response and direct result
        actual = result.get("text_response", result) if isinstance(result, dict) else result
        
        self.assert_result("Execute function with object param (lng_javascript_execute)", expected, actual)
    
    # Test 6: Add function with modern JavaScript and extensive debugging
    async def test_add_debug_function(self):
        """
        GIVEN: I want to test all console logging features
        WHEN: I add a function using lng_javascript_add with comprehensive debugging
        THEN: I should get success confirmation
        """
        # Given: Want comprehensive debugging
        
        # When: Add function with all debugging features
        function_code = '''function debugExample(params) {
            console.log("=== debugExample started ===");
            console.log("Input parameters:", JSON.stringify(params, null, 2));
            
            if (params.debug) {
                console.warn("Debug mode is enabled - showing detailed information");
                console.log("Parameter type:", typeof params);
                console.log("Parameter keys:", Object.keys(params));
            }
            
            const result = {
                input: params,
                timestamp: new Date().toISOString(),
                processed: true,
                debug_info: params.debug ? "Debug mode was active" : "Normal mode"
            };
            
            if (params.simulate_error) {
                console.error("Simulated error condition detected!");
                console.error("Error details:", { reason: "simulate_error flag was set" });
            }
            
            console.log("Final result:", JSON.stringify(result, null, 2));
            console.log("=== debugExample completed ===");
            
            return result;
        }'''
        
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "debugExample",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'debugExample' saved successfully",
            "function_name": "debugExample",
            "storage_path": "mcp_server/config/javascript/debugExample.js"
        }
        
        self.assert_result("Add debug function (lng_javascript_add)", expected, result)
        self.saved_functions.append("debugExample")
    
    # Test 7: Execute debug function with complex object to see all console outputs
    async def test_execute_debug_function(self):
        """
        GIVEN: A 'debugExample' function with comprehensive logging exists
        WHEN: I execute it with complex parameters using lng_javascript_execute
        THEN: I should get the result object and see extensive console logs
        """
        # Given: debugExample function exists
        
        # When: Execute with complex parameters to trigger all logging
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "debugExample",
            "parameters": {
                "debug": True,
                "user": {"name": "TestUser", "age": 30},
                "options": {"verbose": True, "format": "json"},
                "items": ["item1", "item2", "item3"],
                "simulate_error": True
            }
        })
        
        # Then: Should get complex result object
        # We'll check that it's an object with expected structure
        expected_keys = {"input", "timestamp", "processed", "debug_info"}
        actual_result = result.get("text_response", result) if isinstance(result, dict) else result
        
        # Check if result is an object (dict) and has expected keys
        has_expected_structure = (
            isinstance(actual_result, dict) and 
            expected_keys.issubset(set(actual_result.keys()))
        )
        
        self.assert_result("Execute debug function (lng_javascript_execute)", True, has_expected_structure)
    
    # Test 8: List functions after adding several using lng_javascript_list
    async def test_list_multiple_functions(self):
        """
        GIVEN: Multiple functions have been saved (greet, calculateSum, debugExample)
        WHEN: I call lng_javascript_list
        THEN: I should get all three functions in the list
        """
        # Given: Multiple functions exist
        
        # When: List functions using dedicated list tool
        result = await self.run_javascript_tool("lng_javascript_list", {})
        
        # Then: Should get all functions
        expected_functions = {"greet", "calculateSum", "debugExample"}
        actual_functions = set(result.get("functions", []))
        
        # Check if all expected functions are present
        contains_all = expected_functions.issubset(actual_functions)
        
        self.assert_result("List multiple functions (lng_javascript_list)", True, contains_all)
    
    # Test 9: Error handling - Function not found using lng_javascript_execute
    async def test_execute_nonexistent_function(self):
        """
        GIVEN: No function named 'nonexistent' exists
        WHEN: I try to execute it using lng_javascript_execute
        THEN: I should get an error message about function not found
        """
        # Given: Function doesn't exist
        
        # When: Try to execute nonexistent function
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "nonexistent",
            "parameters": "test"
        })
        
        # Then: Should get error message
        expected_error = "Function nonexistent not found. Use lng_javascript_add to save it first."
        actual_error = result.get("error", "")
        
        self.assert_result("Execute nonexistent function error (lng_javascript_execute)", expected_error, actual_error)
    
    # Test 10: Error handling - Invalid function code using lng_javascript_add
    async def test_add_invalid_function(self):
        """
        GIVEN: I want to add a function with invalid syntax
        WHEN: I try to add a function that doesn't match the function name using lng_javascript_add
        THEN: I should get a validation error
        """
        # Given: Want to add invalid function
        
        # When: Try to add function with wrong name
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "wrongName",
            "function_code": "function correctName(params) { return params; }"
        })
        
        # Then: Should get validation error
        expected_error = "Function code must contain a declared function named wrongName. Arrow functions are not allowed."
        actual_error = result.get("error", "")
        
        self.assert_result("Add invalid function name (lng_javascript_add)", expected_error, actual_error)
    
    # Test 11: Test batch execution using lng_batch_run with JavaScript tools
    async def test_batch_execution(self):
        """
        GIVEN: I want to create and execute a function in one batch
        WHEN: I use lng_batch_run to add and execute a function
        THEN: I should get the execution result
        """
        # Given: Want to use batch execution
        
        # When: Use batch to add and execute function
        result = await self.run_javascript_tool("lng_batch_run", {
            "pipeline": [
                {
                    "tool": "lng_javascript_add",
                    "params": {
                        "function_name": "batchTest",
                        "function_code": "function batchTest(params) { console.log('Batch test:', params); return 'Batch executed: ' + JSON.stringify(params); }"
                    },
                    "output": "add_result"
                },
                {
                    "tool": "lng_javascript_execute", 
                    "params": {
                        "function_name": "batchTest",
                        "parameters": {"message": "batch test successful"}
                    },
                    "output": "exec_result"
                }
            ],
            "final_result": "{! exec_result !}"
        })
        
        # Then: Should get execution result
        expected_text = "Batch executed: "
        actual_result = str(result.get("result", ""))
        contains_expected = expected_text in actual_result
        
        self.assert_result("Batch execution (lng_batch_run)", True, contains_expected)
        self.saved_functions.append("batchTest")

    async def run_all_tests(self):
        """Run all test cases in sequence."""
        logger.info("🚀 Starting lng_javascript separate tools comprehensive testing")
        logger.info("=" * 70)
        
        # Initialize tools
        result = initialize_tools()
        if result:
            await result
        
        # Run all tests in sequence
        test_methods = [
            self.test_list_empty_functions,
            self.test_add_simple_function,
            self.test_execute_function_string_param,
            self.test_add_complex_function_with_logging,
            self.test_execute_function_object_param,
            self.test_add_debug_function,
            self.test_execute_debug_function,
            self.test_list_multiple_functions,
            self.test_execute_nonexistent_function,
            self.test_add_invalid_function,
            self.test_batch_execution
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"❌ Test {test_method.__name__} failed with exception: {e}")
                self.test_results.append({
                    "test_name": test_method.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        # Print summary
        self.print_test_summary()
        
        # Cleanup
        await self.cleanup_functions()
    
    def print_test_summary(self):
        """Print a comprehensive test summary."""
        logger.info("=" * 70)
        logger.info("🎯 TEST SUMMARY - lng_javascript separate tools")
        logger.info("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get("success", False))
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.get("success", False):
                    logger.info(f"  - {result['test_name']}")
                    if "error" in result:
                        logger.info(f"    Error: {result['error']}")
        
        logger.info("=" * 70)
    
    # Test 1: List functions when none exist
    async def test_list_empty_functions(self):
        """
        GIVEN: No JavaScript functions have been saved
        WHEN: I call the list command  
        THEN: I should get an empty functions list
        """
        # Given: Fresh state (handled by test setup)
        
        # When: List functions using dedicated tool
        result = await self.run_javascript_tool("lng_javascript_list", {})
        
        # Then: Should get empty list or existing functions structure
        # We check for the expected structure since other tests may have created functions
        has_expected_structure = (
            isinstance(result, dict) and
            "functions" in result and
            isinstance(result["functions"], list)
        )
        
        self.assert_result("List functions structure", True, has_expected_structure)
    
    # Test 2: Add a simple function
    async def test_add_simple_function(self):
        """
        GIVEN: No function named 'greet' exists
        WHEN: I add a simple greeting function
        THEN: I should get a success message with function details
        """
        # Given: No function exists (implicit)
        
        # When: Add simple function with console logging
        function_code = 'function greet(params) { console.log("Greeting called:", params); return "Hello, " + params; }'
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "greet",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'greet' saved successfully",
            "function_name": "greet",
            "storage_path": "mcp_server/config/javascript/greet.js"
        }
        
        self.assert_result("Add simple function", expected, result)
        self.saved_functions.append("greet")
    
    # Test 3: Execute simple function with string parameter
    async def test_execute_function_string_param(self):
        """
        GIVEN: A 'greet' function has been saved
        WHEN: I execute it with a string parameter
        THEN: I should get the greeting result
        """
        # Given: greet function exists (from previous test)
        
        # When: Execute with string parameter using dedicated execution tool
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "greet",
            "parameters": "World"
        })
        
        # Then: Should get greeting result
        expected = "Hello, World"
        actual = result.get("text_response", result)
        
        self.assert_result("Execute function with string param", expected, actual)
    
    # Test 4: Add complex function with JSON parameters
    async def test_add_complex_function(self):
        """
        GIVEN: I want to create a function that handles JSON objects
        WHEN: I add a function that calculates sum from object properties
        THEN: I should get success confirmation
        """
        # Given: Want to handle JSON objects with console logging
        
        # When: Add complex function with logging
        function_code = 'function calculateSum(params) { console.log("Calculating:", params); const result = params.a + params.b; console.log("Result:", result); return result; }'
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "calculateSum",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'calculateSum' saved successfully",
            "function_name": "calculateSum",
            "storage_path": "mcp_server/config/javascript/calculateSum.js"
        }
        
        self.assert_result("Add complex function", expected, result)
        self.saved_functions.append("calculateSum")
    
    # Test 5: Execute function with JSON parameters
    async def test_execute_function_json_param(self):
        """
        GIVEN: A 'calculateSum' function has been saved
        WHEN: I execute it with JSON parameters
        THEN: I should get the calculated sum
        """
        # Given: calculateSum function exists
        
        # When: Execute with JSON parameters
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "calculateSum",
            "parameters": {"a": 5, "b": 3}
        })
        
        # Then: Should get sum result
        expected = 8
        # Handle both string response and direct result
        actual = result.get("text_response", result) if isinstance(result, dict) else result
        
        self.assert_result("Execute function with JSON param", expected, actual)
    
    # Test 6: Add function with modern JavaScript features
    async def test_add_modern_javascript_function(self):
        """
        GIVEN: I want to use modern JavaScript features
        WHEN: I add a function using array methods and destructuring
        THEN: I should get success confirmation
        """
        # Given: Want to use modern JS features
        
        # When: Add function with modern features
        function_code = '''function processArray(params) {
            const { numbers, operation } = params;
            console.log(`Processing array with ${numbers.length} numbers, operation: ${operation}`);
            if (operation === 'sum') {
                return numbers.reduce((a, b) => a + b, 0);
            } else if (operation === 'average') {
                const sum = numbers.reduce((a, b) => a + b, 0);
                return sum / numbers.length;
            }
            return 'Unknown operation';
        }'''
        
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "processArray",
            "function_code": function_code
        })
        
        # Then: Should get success message
        expected = {
            "message": "Function 'processArray' saved successfully",
            "function_name": "processArray",
            "storage_path": "mcp_server/config/javascript/processArray.js"
        }
        
        self.assert_result("Add modern JavaScript function", expected, result)
        self.saved_functions.append("processArray")
    
    # Test 7: Execute modern JavaScript function
    async def test_execute_modern_function(self):
        """
        GIVEN: A 'processArray' function with modern JS features exists
        WHEN: I execute it with array data for sum operation
        THEN: I should get the sum of the array
        """
        # Given: processArray function exists
        
        # When: Execute with array sum operation
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "processArray",
            "parameters": {"numbers": [1, 2, 3, 4, 5], "operation": "sum"}
        })
        
        # Then: Should get sum result
        expected = 15
        # Handle both string response and direct result
        actual = result.get("text_response", result) if isinstance(result, dict) else result
        
        self.assert_result("Execute modern function (sum)", expected, actual)
    
    # Test 8: List functions after adding several
    async def test_list_multiple_functions(self):
        """
        GIVEN: Multiple functions have been saved (greet, calculateSum, processArray)
        WHEN: I call the list command
        THEN: I should get all three functions in the list
        """
        # Given: Multiple functions exist
        
        # When: List functions
        result = await self.run_javascript_tool("lng_javascript_list", {})
        
        # Then: Should get all functions
        expected_functions = {"greet", "calculateSum", "processArray"}
        actual_functions = set(result.get("functions", []))
        
        # Check if all expected functions are present
        contains_all = expected_functions.issubset(actual_functions)
        
        self.assert_result("List multiple functions", True, contains_all)
    
    # Test 9: Error handling - Function not found
    async def test_execute_nonexistent_function(self):
        """
        GIVEN: No function named 'nonexistent' exists
        WHEN: I try to execute it
        THEN: I should get an error message about function not found
        """
        # Given: Function doesn't exist
        
        # When: Try to execute nonexistent function
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "function_name": "nonexistent",
            "parameters": "test"
        })
        
        # Then: Should get error message
        expected_error = "Function nonexistent not found. Use lng_javascript_add to save it first."
        actual_error = result.get("error", "")
        
        self.assert_result("Execute nonexistent function error", expected_error, actual_error)
    
    # Test 10: Error handling - Invalid function code
    async def test_add_invalid_function(self):
        """
        GIVEN: I want to add a function with invalid syntax
        WHEN: I try to add a function that doesn't match the function name
        THEN: I should get a validation error
        """
        # Given: Want to add invalid function
        
        # When: Try to add function with wrong name
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "wrongName",
            "function_code": "function correctName(params) { return params; }"
        })
        
        # Then: Should get validation error
        expected_error = "Function code must contain a declared function named wrongName. Arrow functions are not allowed."
        actual_error = result.get("error", "")
        
        self.assert_result("Add invalid function name", expected_error, actual_error)
    
    # Test 11: Error handling - Missing parameters
    async def test_missing_command_parameter(self):
        """
        GIVEN: I want to call the tool
        WHEN: I try to execute function without function_name
        THEN: I should get an error about missing parameter
        """
        # Given: Want to execute function
        
        # When: Call execute without function_name
        result = await self.run_javascript_tool("lng_javascript_execute", {
            "parameters": "test"
        })
        
        # Then: Should get missing parameter error
        expected_error = "function_name is required"
        actual_error = result.get("error", "")
        
        self.assert_result("Missing function_name parameter", expected_error, actual_error)
    
    # Test 12: Edge case - Empty function code
    async def test_add_empty_function_code(self):
        """
        GIVEN: I want to add a function
        WHEN: I provide empty function code
        THEN: I should get an error about missing function code
        """
        # Given: Want to add function
        
        # When: Provide empty function code
        result = await self.run_javascript_tool("lng_javascript_add", {
            "function_name": "emptyFunc",
            "function_code": ""
        })
        
        # Then: Should get missing function code error
        expected_error = "function_code is required"
        actual_error = result.get("error", "")
        
        self.assert_result("Add empty function code", expected_error, actual_error)

    async def run_all_tests(self):
        """Run all test cases in sequence."""
        logger.info("🚀 Starting lng_javascript comprehensive testing")
        logger.info("=" * 60)
        
        # Initialize tools
        result = initialize_tools()
        if result:
            await result
        
        # Run all tests in sequence
        test_methods = [
            self.test_list_empty_functions,
            self.test_add_simple_function,
            self.test_execute_function_string_param,
            self.test_add_complex_function,
            self.test_execute_function_json_param,
            self.test_add_modern_javascript_function,
            self.test_execute_modern_function,
            self.test_list_multiple_functions,
            self.test_execute_nonexistent_function,
            self.test_add_invalid_function,
            self.test_missing_command_parameter,
            self.test_add_empty_function_code
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"❌ Test {test_method.__name__} failed with exception: {e}")
                self.test_results.append({
                    "test_name": test_method.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        # Print summary
        self.print_test_summary()
        
        # Cleanup
        await self.cleanup_functions()
    
    def print_test_summary(self):
        """Print a comprehensive test summary."""
        logger.info("=" * 60)
        logger.info("🎯 TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get("success", False))
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.get("success", False):
                    logger.info(f"  - {result['test_name']}")
                    if "error" in result:
                        logger.info(f"    Error: {result['error']}")
        
        logger.info("=" * 60)


async def main():
    """Main test execution function."""
    tester = JavaScriptSeparateToolsTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
    except Exception as e:
        logger.error(f"💥 Critical error during testing: {e}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        logger.info("🏁 Testing completed")


if __name__ == "__main__":
    asyncio.run(main())