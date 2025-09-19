#!/usr/bin/env python3
"""
Approval Tests for expressions system - converting test2.py to structured approach
"""

import sys
import os
import unittest
import json
from pathlib import Path

# Add the project root to the path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from mcp_server.pipeline.expressions import evaluate_expression, substitute_expressions, ExpressionEvaluationError


class TestExpressionsApproval(unittest.TestCase):
    """Approval Tests for expressions system."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(__file__).parent / "test_data_expressions"
        self.test_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test files if needed
        pass
    
    def _is_valid_json(self, text):
        """Helper method to check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (ValueError, TypeError):
            return False
    
    def test_python_list_flattening(self):
        """Python list flattening"""
        
        # Test data (from original test2.py)
        variables = {
            'all_file_contents': [
                [{'name': 'file1', 'value': 1}, {'name': 'file2', 'value': 2}],
                [{'name': 'file3', 'value': 3}]
            ],
            'simple_var': 'hello world',
            'number_var': 42,
            'list_numbers': [1, 2, 3, 4, 5],
            'nested_obj': {'level1': {'level2': {'value': 'deep_value'}}}
        }
        
        # Execute the expression
        py_expr = "[! [item for sublist in all_file_contents for item in sublist] !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_list_flattening",
            "expression": py_expr,
            "input_variables": {
                "all_file_contents": variables['all_file_contents'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if hasattr(result, '__len__') else None
            },
            "validation": {
                "expected_length": 3,
                "actual_length": len(result),
                "length_matches": len(result) == 3,
                "expected_items": [
                    {'name': 'file1', 'value': 1}, 
                    {'name': 'file2', 'value': 2}, 
                    {'name': 'file3', 'value': 3}
                ],
                "items_match": result == [
                    {'name': 'file1', 'value': 1}, 
                    {'name': 'file2', 'value': 2}, 
                    {'name': 'file3', 'value': 3}
                ]
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_list_flattening",
    "expression": "[! [item for sublist in all_file_contents for item in sublist] !]",
    "input_variables": {
        "all_file_contents": [
            [
                {
                    "name": "file1",
                    "value": 1
                },
                {
                    "name": "file2",
                    "value": 2
                }
            ],
            [
                {
                    "name": "file3",
                    "value": 3
                }
            ]
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": [
            {
                "name": "file1",
                "value": 1
            },
            {
                "name": "file2",
                "value": 2
            },
            {
                "name": "file3",
                "value": 3
            }
        ],
        "result_type": "<class 'list'>",
        "result_length": 3
    },
    "validation": {
        "expected_length": 3,
        "actual_length": 3,
        "length_matches": true,
        "expected_items": [
            {
                "name": "file1",
                "value": 1
            },
            {
                "name": "file2",
                "value": 2
            },
            {
                "name": "file3",
                "value": 3
            }
        ],
        "items_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 1 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(len(result), 3, "Should flatten to 3 items")
        self.assertTrue(test_result["validation"]["length_matches"], "Length validation should pass")
        self.assertTrue(test_result["validation"]["items_match"], "Items should match expected")

    def test_javascript_simple_variable(self):
        """JavaScript expression (simple variable)"""
        
        # Test data (from original test2.py)
        variables = {
            'all_file_contents': [
                [{'name': 'file1', 'value': 1}, {'name': 'file2', 'value': 2}],
                [{'name': 'file3', 'value': 3}]
            ],
            'simple_var': 'hello world',
            'number_var': 42,
            'list_numbers': [1, 2, 3, 4, 5],
            'nested_obj': {'level1': {'level2': {'value': 'deep_value'}}}
        }
        
        # Execute the expression
        js_expr = "{! simple_var !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_simple_variable",
            "expression": js_expr,
            "input_variables": {
                "simple_var": variables['simple_var'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "hello world",
                "actual_value": result,
                "values_match": result == "hello world",
                "is_string": isinstance(result, str),
                "simple_variable_access": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "javascript_simple_variable",
    "expression": "{! simple_var !}",
    "input_variables": {
        "simple_var": "hello world",
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "hello world",
        "result_type": "<class 'str'>",
        "result_length": 11
    },
    "validation": {
        "expected_value": "hello world",
        "actual_value": "hello world",
        "values_match": true,
        "is_string": true,
        "simple_variable_access": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 2 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "hello world", "Should return simple_var value")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["is_string"], "Result should be string")

    def test_python_simple_variable(self):
        """Python simple variable access"""
        
        # Test data (from original test2.py Test 3)
        variables = {
            'simple_var': 'hello world',
            'number_var': 42,
            'list_numbers': [1, 2, 3, 4, 5]
        }
        
        # Execute the expression
        py_expr = "[! simple_var !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_simple_variable",
            "expression": py_expr,
            "input_variables": {
                "simple_var": variables['simple_var'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "hello world",
                "actual_value": result,
                "values_match": result == "hello world",
                "is_string": isinstance(result, str),
                "simple_variable_access": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_simple_variable",
    "expression": "[! simple_var !]",
    "input_variables": {
        "simple_var": "hello world",
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "hello world",
        "result_type": "<class 'str'>",
        "result_length": 11
    },
    "validation": {
        "expected_value": "hello world",
        "actual_value": "hello world",
        "values_match": true,
        "is_string": true,
        "simple_variable_access": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Python simple variable test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "hello world", "Should return simple_var value")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["is_string"], "Result should be string")

    def test_javascript_json_stringify(self):
        """JavaScript JSON.stringify functionality"""
        
        # Test data (from original test2.py Test 4)
        variables = {
            'all_file_contents': [
                [{'name': 'file1', 'value': 1}, {'name': 'file2', 'value': 2}],
                [{'name': 'file3', 'value': 3}]
            ],
            'simple_var': 'hello world'
        }
        
        # Execute the expression
        js_expr = "{! JSON.stringify(all_file_contents) !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_json_stringify",
            "expression": js_expr,
            "input_variables": {
                "all_file_contents": variables['all_file_contents'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None,
                "is_valid_json": self._is_valid_json(result)
            },
            "validation": {
                "expected_type": "string",
                "actual_type": type(result).__name__,
                "is_string": isinstance(result, str),
                "json_stringify_operation": True,
                "contains_expected_data": "file1" in result and "file3" in result if isinstance(result, str) else False
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot (result will vary by JSON serialization but structure is consistent)
        expected_result = """{
    "test_name": "javascript_json_stringify",
    "expression": "{! JSON.stringify(all_file_contents) !}",
    "input_variables": {
        "all_file_contents": [
            [
                {
                    "name": "file1",
                    "value": 1
                },
                {
                    "name": "file2", 
                    "value": 2
                }
            ],
            [
                {
                    "name": "file3",
                    "value": 3
                }
            ]
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "[[{\\"name\\":\\"file1\\",\\"value\\":1},{\\"name\\":\\"file2\\",\\"value\\":2}],[{\\"name\\":\\"file3\\",\\"value\\":3}]]",
        "result_length": 86,
        "result_type": "<class 'str'>",
        "is_valid_json": true
    },
    "validation": {
        "actual_type": "str",
        "contains_expected_data": true,
        "expected_type": "string",
        "is_string": true,
        "json_stringify_operation": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"JavaScript JSON.stringify test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertIsInstance(result, str, "JSON.stringify should return a string")
        self.assertTrue(self._is_valid_json(result), "Result should be valid JSON")
        self.assertIn("file1", result, "Should contain file1 data")
        self.assertIn("file3", result, "Should contain file3 data")

    def test_python_len_function(self):
        """Python len() function"""
        
        # Test data (from original test2.py Test 5)
        variables = {
            'all_file_contents': [
                [{'name': 'file1', 'value': 1}, {'name': 'file2', 'value': 2}],
                [{'name': 'file3', 'value': 3}]
            ],
            'simple_var': 'hello world'
        }
        
        # Execute the expression
        py_expr = "[! len(all_file_contents) !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_len_function",
            "expression": py_expr,
            "input_variables": {
                "all_file_contents": variables['all_file_contents'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "is_integer": isinstance(result, int)
            },
            "validation": {
                "expected_value": 2,
                "actual_value": result,
                "values_match": result == 2,
                "is_integer": isinstance(result, int),
                "len_function_call": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_len_function",
    "expression": "[! len(all_file_contents) !]",
    "input_variables": {
        "all_file_contents": [
            [
                {
                    "name": "file1",
                    "value": 1
                },
                {
                    "name": "file2",
                    "value": 2
                }
            ],
            [
                {
                    "name": "file3",
                    "value": 3
                }
            ]
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "is_integer": true,
        "result": 2,
        "result_type": "<class 'int'>"
    },
    "validation": {
        "actual_value": 2,
        "expected_value": 2,
        "is_integer": true,
        "len_function_call": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Python len() function test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, 2, "len(all_file_contents) should return 2")
        self.assertIsInstance(result, int, "len() should return an integer")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_javascript_ternary_operator(self):
        """JavaScript ternary operator"""
        
        # Test data (from original test2.py Test 6) 
        variables = {
            'numbers': [1, 2, 3, 4, 5],
            'text': 'Hello World Testing',
            'score': 85,
            'items': [
                {'name': 'item1', 'price': 10.5, 'category': 'A'},
                {'name': 'item2', 'price': 25.0, 'category': 'B'},
                {'name': 'item3', 'price': 15.5, 'category': 'A'}
            ]
        }
        
        # Execute the expression
        js_expr = "{! score >= 90 ? 'Excellent' : 'Good' !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_ternary_operator",
            "expression": js_expr,
            "input_variables": {
                "score": variables['score'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "Good",
                "actual_value": result,
                "values_match": result == "Good",
                "is_string": isinstance(result, str),
                "ternary_operator_logic": True,
                "condition_evaluated": "score >= 90 evaluated to False, returned 'Good'"
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "javascript_ternary_operator",
    "expression": "{! score >= 90 ? 'Excellent' : 'Good' !}",
    "input_variables": {
        "score": 85,
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "Good",
        "result_length": 4,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_value": "Good",
        "condition_evaluated": "score >= 90 evaluated to False, returned 'Good'",
        "expected_value": "Good",
        "is_string": true,
        "ternary_operator_logic": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"JavaScript ternary operator test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "Good", "score 85 should trigger 'Good' response")
        self.assertIsInstance(result, str, "Ternary result should be string")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_javascript_complex_nested_access(self):
        """JavaScript complex nested data access"""
        
        # Test data (from original test2.py Test 9)
        variables = {
            'data': {
                'users': [
                    {'id': 1, 'profile': {'name': 'Alice', 'settings': {'theme': 'dark'}}},
                    {'id': 2, 'profile': {'name': 'Bob', 'settings': {'theme': 'light'}}}
                ]
            }
        }
        
        # Execute the expression
        js_expr = "{! data.users.find(u => u.id === 2).profile.name !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_complex_nested_access",
            "expression": js_expr,
            "input_variables": {
                "data": variables['data'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "Bob",
                "actual_value": result,
                "values_match": result == "Bob",
                "is_string": isinstance(result, str),
                "complex_nested_access": True,
                "javascript_find_method": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "javascript_complex_nested_access",
    "expression": "{! data.users.find(u => u.id === 2).profile.name !}",
    "input_variables": {
        "data": {
            "users": [
                {
                    "id": 1,
                    "profile": {
                        "name": "Alice",
                        "settings": {
                            "theme": "dark"
                        }
                    }
                },
                {
                    "id": 2,
                    "profile": {
                        "name": "Bob",
                        "settings": {
                            "theme": "light"
                        }
                    }
                }
            ]
        },
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "Bob",
        "result_length": 3,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_value": "Bob",
        "complex_nested_access": true,
        "expected_value": "Bob",
        "is_string": true,
        "javascript_find_method": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"JavaScript complex nested access test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "Bob", "Should find user with id=2 and return Bob")
        self.assertIsInstance(result, str, "Result should be string")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_python_nested_access(self):
        """Python equivalent of nested access"""
        
        # Test data (from original test2.py Test 10)
        variables = {
            'data': {
                'users': [
                    {'id': 1, 'profile': {'name': 'Alice', 'settings': {'theme': 'dark'}}},
                    {'id': 2, 'profile': {'name': 'Bob', 'settings': {'theme': 'light'}}}
                ]
            }
        }
        
        # Execute the expression (Direct access to second user - index 1)
        py_expr = "[! data['users'][1]['profile']['name'] !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_nested_access",
            "expression": py_expr,
            "input_variables": {
                "data": variables['data'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "Bob",
                "actual_value": result,
                "values_match": result == "Bob",
                "is_string": isinstance(result, str),
                "nested_access": True,
                "python_bracket_notation": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_nested_access",
    "expression": "[! data['users'][1]['profile']['name'] !]",
    "input_variables": {
        "data": {
            "users": [
                {
                    "id": 1,
                    "profile": {
                        "name": "Alice",
                        "settings": {
                            "theme": "dark"
                        }
                    }
                },
                {
                    "id": 2,
                    "profile": {
                        "name": "Bob",
                        "settings": {
                            "theme": "light"
                        }
                    }
                }
            ]
        },
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "Bob",
        "result_length": 3,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_value": "Bob",
        "expected_value": "Bob",
        "is_string": true,
        "nested_access": true,
        "python_bracket_notation": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Python nested access test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "Bob", "Should access users[1] and return Bob")
        self.assertIsInstance(result, str, "Result should be string")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_mixed_expressions_in_text(self):
        """Mixed expressions in text substitution"""
        
        # Test data (from original test2.py Test 11)
        variables = {
            'name': 'Alice',
            'age': 30,
            'skills': ['Python', 'JavaScript', 'SQL'],
            'score': 95
        }
        
        # Execute the substitution (using substitute_expressions instead of evaluate_expression)
        text = "Hello {! name !}, you are [! age !] years old and have {! skills.length !} skills. Grade: {! score >= 90 ? 'A' : 'B' !}"
        result = substitute_expressions(text, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "mixed_expressions_in_text",
            "template": text,
            "input_variables": variables,
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "Hello Alice, you are 30 years old and have 3 skills. Grade: A",
                "actual_value": result,
                "values_match": result == "Hello Alice, you are 30 years old and have 3 skills. Grade: A",
                "mixed_substitution": True,
                "javascript_and_python": True,
                "string_template": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "mixed_expressions_in_text",
    "template": "Hello {! name !}, you are [! age !] years old and have {! skills.length !} skills. Grade: {! score >= 90 ? 'A' : 'B' !}",
    "input_variables": {
        "age": 30,
        "name": "Alice",
        "score": 95,
        "skills": [
            "Python",
            "JavaScript",
            "SQL"
        ]
    },
    "execution": {
        "result": "Hello Alice, you are 30 years old and have 3 skills. Grade: A",
        "result_length": 61,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_value": "Hello Alice, you are 30 years old and have 3 skills. Grade: A",
        "expected_value": "Hello Alice, you are 30 years old and have 3 skills. Grade: A",
        "javascript_and_python": true,
        "mixed_substitution": true,
        "string_template": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Mixed expressions in text test result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        expected_final = "Hello Alice, you are 30 years old and have 3 skills. Grade: A"
        self.assertEqual(result, expected_final, "Should substitute all mixed expressions correctly")
        self.assertIsInstance(result, str, "Result should be string")
        self.assertIn("Alice", result, "Should contain name")
        self.assertIn("30", result, "Should contain age")
        self.assertIn("3 skills", result, "Should contain skills count")
        self.assertIn("Grade: A", result, "Should contain correct grade")

    def test_json_result_type(self):
        """JSON result type test"""
        
        # Test data (from original test2.py Test 12) 
        variables = {
            'name': 'Alice',
            'age': 30,
            'skills': ['Python', 'JavaScript', 'SQL'],
            'score': 95
        }
        
        # Execute the expression with JSON result type
        py_expr = "[! skills[:2] !]"  # First 2 skills
        result = evaluate_expression(py_expr, variables, expected_result_type="json")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "json_result_type",
            "expression": py_expr,
            "input_variables": {
                "skills": variables['skills'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None,
                "expected_result_type": "json",
                "is_valid_json": self._is_valid_json(result)
            },
            "validation": {
                "expected_parsed_value": ["Python", "JavaScript"],
                "actual_parsed_value": json.loads(result) if isinstance(result, str) else None,
                "values_match": json.loads(result) == ["Python", "JavaScript"] if isinstance(result, str) else False,
                "is_string": isinstance(result, str),
                "json_result_type": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "json_result_type",
    "expression": "[! skills[:2] !]",
    "input_variables": {
        "skills": [
            "Python",
            "JavaScript",
            "SQL"
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "expected_result_type": "json",
        "is_valid_json": true,
        "result": "[\\"Python\\", \\"JavaScript\\"]",
        "result_length": 24,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_parsed_value": [
            "Python",
            "JavaScript"
        ],
        "expected_parsed_value": [
            "Python",
            "JavaScript"
        ],
        "is_string": true,
        "json_result_type": true,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"JSON result type test doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertIsInstance(result, str, "Result should be string (JSON)")
        self.assertTrue(self._is_valid_json(result), "Result should be valid JSON")
        parsed = json.loads(result)
        self.assertEqual(parsed, ["Python", "JavaScript"], "Parsed JSON should match expected array")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_javascript_object_property_access(self):
        """JavaScript object property access"""
        
        # Test data (from original test2.py)
        variables = {
            'nested_obj': {'level1': {'level2': {'value': 'deep_value'}}},
            'simple_var': 'hello world',
            'number_var': 42
        }
        
        # Execute the expression
        js_expr = "{! nested_obj.level1.level2.value !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_object_property_access",
            "expression": js_expr,
            "input_variables": {
                "nested_obj": variables['nested_obj'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "deep_value",
                "actual_value": result,
                "values_match": result == "deep_value",
                "is_string": isinstance(result, str)
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "javascript_object_property_access",
    "expression": "{! nested_obj.level1.level2.value !}",
    "input_variables": {
        "nested_obj": {
            "level1": {
                "level2": {
                    "value": "deep_value"
                }
            }
        },
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": "deep_value",
        "result_type": "<class 'str'>",
        "result_length": 10
    },
    "validation": {
        "expected_value": "deep_value",
        "actual_value": "deep_value",
        "values_match": true,
        "is_string": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 2 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, "deep_value", "Should return deep_value")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["is_string"], "Result should be string")

    def test_python_math_operations(self):
        """Python mathematical operations"""
        
        # Test data (from original test2.py)
        variables = {
            'number_var': 42,
            'list_numbers': [1, 2, 3, 4, 5],
            'simple_var': 'hello world'
        }
        
        # Execute the expression
        py_expr = "[! number_var + sum(list_numbers) !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_math_operations",
            "expression": py_expr,
            "input_variables": {
                "number_var": variables['number_var'],
                "list_numbers": variables['list_numbers'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "calculation": "42 + sum([1, 2, 3, 4, 5]) = 42 + 15 = 57"
            },
            "validation": {
                "expected_value": 57,
                "actual_value": result,
                "values_match": result == 57,
                "is_integer": isinstance(result, int),
                "calculation_correct": result == (42 + sum([1, 2, 3, 4, 5]))
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_math_operations",
    "expression": "[! number_var + sum(list_numbers) !]",
    "input_variables": {
        "number_var": 42,
        "list_numbers": [
            1,
            2,
            3,
            4,
            5
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": 57,
        "result_type": "<class 'int'>",
        "calculation": "42 + sum([1, 2, 3, 4, 5]) = 42 + 15 = 57"
    },
    "validation": {
        "expected_value": 57,
        "actual_value": 57,
        "values_match": true,
        "is_integer": true,
        "calculation_correct": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 3 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, 57, "Should return 42 + 15 = 57")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["calculation_correct"], "Calculation should be correct")

    def test_javascript_array_operations(self):
        """JavaScript array operations"""
        
        # Test data (from original test2.py)
        variables = {
            'list_numbers': [1, 2, 3, 4, 5],
            'number_var': 42,
            'simple_var': 'hello world'
        }
        
        # Execute the expression
        js_expr = "{! list_numbers.length + number_var !}"
        result = evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "javascript_array_operations",
            "expression": js_expr,
            "input_variables": {
                "list_numbers": variables['list_numbers'],
                "number_var": variables['number_var'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "calculation": "list_numbers.length (5) + number_var (42) = 47"
            },
            "validation": {
                "expected_value": 47,
                "actual_value": result,
                "values_match": result == 47,
                "is_numeric": isinstance(result, (int, float)),
                "calculation_correct": result == (len([1, 2, 3, 4, 5]) + 42)
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "javascript_array_operations",
    "expression": "{! list_numbers.length + number_var !}",
    "input_variables": {
        "list_numbers": [
            1,
            2,
            3,
            4,
            5
        ],
        "number_var": 42,
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": 47,
        "result_type": "<class 'int'>",
        "calculation": "list_numbers.length (5) + number_var (42) = 47"
    },
    "validation": {
        "expected_value": 47,
        "actual_value": 47,
        "values_match": true,
        "is_numeric": true,
        "calculation_correct": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 4 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, 47, "Should return 5 + 42 = 47")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["calculation_correct"], "Calculation should be correct")

    def test_python_filter_and_sum(self):
        """Python filter and sum"""
        
        # Test data (from original test2.py advanced expressions)
        variables = {
            'numbers': [1, 2, 3, 4, 5],
            'text': 'Hello World Testing',
            'score': 85,
            'items': [
                {'name': 'item1', 'price': 10.5, 'category': 'A'},
                {'name': 'item2', 'price': 25.0, 'category': 'B'},
                {'name': 'item3', 'price': 15.5, 'category': 'A'}
            ]
        }
        
        # Execute the expression
        py_expr = "[! sum(item['price'] for item in items if item['category'] == 'A') !]"
        result = evaluate_expression(py_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "python_filter_and_sum",
            "expression": py_expr,
            "input_variables": {
                "items": variables['items'],
                "category_A_items": [item for item in variables['items'] if item['category'] == 'A'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "calculation": "sum of prices for category 'A': 10.5 + 15.5 = 26.0"
            },
            "validation": {
                "expected_value": 26.0,
                "actual_value": result,
                "values_match": result == 26.0,
                "is_float": isinstance(result, float),
                "calculation_correct": result == sum(item['price'] for item in variables['items'] if item['category'] == 'A')
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "python_filter_and_sum",
    "expression": "[! sum(item['price'] for item in items if item['category'] == 'A') !]",
    "input_variables": {
        "items": [
            {
                "name": "item1",
                "price": 10.5,
                "category": "A"
            },
            {
                "name": "item2",
                "price": 25.0,
                "category": "B"
            },
            {
                "name": "item3",
                "price": 15.5,
                "category": "A"
            }
        ],
        "category_A_items": [
            {
                "name": "item1",
                "price": 10.5,
                "category": "A"
            },
            {
                "name": "item3",
                "price": 15.5,
                "category": "A"
            }
        ],
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "result": 26.0,
        "result_type": "<class 'float'>",
        "calculation": "sum of prices for category 'A': 10.5 + 15.5 = 26.0"
    },
    "validation": {
        "expected_value": 26.0,
        "actual_value": 26.0,
        "values_match": true,
        "is_float": true,
        "calculation_correct": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 7 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertEqual(result, 26.0, "Should return 26.0 (10.5 + 15.5)")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["calculation_correct"], "Filter and sum should be correct")

    def test_recursive_substitution(self):
        """Recursive expression substitution"""
        
        # Test data (from original test2.py recursive expressions)
        variables = {
            'data1': "Some text {! data3 !} end", 
            'data2': "bla bla", 
            'data3': "qwe {! data2 !} asd"
        }
        
        # Execute the substitution
        text = "{! data1 !} + {! data2 !}"
        result = substitute_expressions(text, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "recursive_substitution",
            "template": text,
            "input_variables": variables,
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "steps": {
                    "step_1": "data3 -> 'qwe {! data2 !} asd' -> 'qwe bla bla asd'",
                    "step_2": "data1 -> 'Some text {! data3 !} end' -> 'Some text qwe bla bla asd end'",
                    "step_3": "Full template -> 'Some text qwe bla bla asd end + bla bla'"
                }
            },
            "validation": {
                "expected_value": "Some text qwe bla bla asd end + bla bla",
                "actual_value": result,
                "values_match": result == "Some text qwe bla bla asd end + bla bla",
                "is_string": isinstance(result, str),
                "recursive_depth": 2
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "recursive_substitution",
    "template": "{! data1 !} + {! data2 !}",
    "input_variables": {
        "data1": "Some text {! data3 !} end",
        "data2": "bla bla",
        "data3": "qwe {! data2 !} asd"
    },
    "execution": {
        "result": "Some text qwe bla bla asd end + bla bla",
        "result_type": "<class 'str'>",
        "steps": {
            "step_1": "data3 -> 'qwe {! data2 !} asd' -> 'qwe bla bla asd'",
            "step_2": "data1 -> 'Some text {! data3 !} end' -> 'Some text qwe bla bla asd end'",
            "step_3": "Full template -> 'Some text qwe bla bla asd end + bla bla'"
        }
    },
    "validation": {
        "expected_value": "Some text qwe bla bla asd end + bla bla",
        "actual_value": "Some text qwe bla bla asd end + bla bla",
        "values_match": true,
        "is_string": true,
        "recursive_depth": 2
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 16 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        expected_final = "Some text qwe bla bla asd end + bla bla"
        self.assertEqual(result, expected_final, "Should handle recursive substitution correctly")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["is_string"], "Result should be string")

    def test_error_handling_invalid_javascript(self):
        """Invalid JavaScript syntax error handling"""
        
        # Test data
        variables = {
            'name': 'Alice',
            'age': 30,
            'skills': ['Python', 'JavaScript', 'SQL'],
            'score': 95
        }
        
        # Execute the expression (should fail)
        js_expr = "{! invalid.syntax.. !}"
        
        # This should raise an exception
        with self.assertRaises(Exception) as context:
            evaluate_expression(js_expr, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "error_handling_invalid_javascript",
            "expression": js_expr,
            "input_variables": {
                "note": "Variables provided but irrelevant for syntax error"
            },
            "execution": {
                "result": "EXCEPTION_RAISED",
                "exception_type": str(type(context.exception).__name__),
                "exception_message_contains": "invalid.syntax" in str(context.exception) or "syntax" in str(context.exception).lower()
            },
            "validation": {
                "expected_behavior": "Should raise an exception",
                "exception_raised": True,
                "error_handling_correct": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot (flexible for error messages)
        expected_result = """{
    "test_name": "error_handling_invalid_javascript",
    "expression": "{! invalid.syntax.. !}",
    "input_variables": {
        "note": "Variables provided but irrelevant for syntax error"
    },
    "execution": {
        "result": "EXCEPTION_RAISED",
        "exception_type": "ExpressionEvaluationError",
        "exception_message_contains": true
    },
    "validation": {
        "expected_behavior": "Should raise an exception",
        "exception_raised": true,
        "error_handling_correct": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 13 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertTrue(test_result["validation"]["exception_raised"], "Exception should be raised")
        self.assertTrue(test_result["validation"]["error_handling_correct"], "Error handling should work")

    def test_error_handling_invalid_python(self):
        """Invalid Python syntax error handling"""
        
        # Test data
        variables = {'valid_var': 42}
        
        # Execute the expression (should fail)
        exception_raised = False
        exception_type = None
        try:
            result = evaluate_expression("[! invalid syntax here !]", variables, expected_result_type="python")
            result_value = result  # Should not reach here
        except Exception as e:
            exception_raised = True
            exception_type = type(e).__name__
            result_value = None
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "error_handling_invalid_python",
            "expression": "[! invalid syntax here !]",
            "input_variables": {
                "valid_var": variables['valid_var'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "exception_raised": exception_raised,
                "exception_type": exception_type,
                "result": result_value
            },
            "validation": {
                "exception_raised": exception_raised,
                "error_handling_correct": exception_raised and result_value is None,
                "python_syntax_error": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "error_handling_invalid_python",
    "expression": "[! invalid syntax here !]",
    "input_variables": {
        "valid_var": 42,
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "exception_raised": true,
        "exception_type": "ExpressionEvaluationError",
        "result": null
    },
    "validation": {
        "error_handling_correct": true,
        "exception_raised": true,
        "python_syntax_error": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 14 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertTrue(test_result["validation"]["exception_raised"], "Exception should be raised")
        self.assertTrue(test_result["validation"]["error_handling_correct"], "Error handling should work")

    def test_error_handling_undefined_variable(self):
        """Undefined variable error handling"""
        
        # Test data
        variables = {'valid_var': 42}
        
        # Execute the expression (should fail)
        exception_raised = False
        exception_type = None
        try:
            result = evaluate_expression("{! undefined_var !}", variables, expected_result_type="python")
            result_value = result  # Should not reach here
        except Exception as e:
            exception_raised = True
            exception_type = type(e).__name__
            result_value = None
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "error_handling_undefined_variable",
            "expression": "{! undefined_var !}",
            "input_variables": {
                "valid_var": variables['valid_var'],
                "note": "Only showing relevant variables for this test"
            },
            "execution": {
                "exception_raised": exception_raised,
                "exception_type": exception_type,
                "result": result_value
            },
            "validation": {
                "exception_raised": exception_raised,
                "error_handling_correct": exception_raised and result_value is None,
                "undefined_variable_error": True
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "error_handling_undefined_variable",
    "expression": "{! undefined_var !}",
    "input_variables": {
        "valid_var": 42,
        "note": "Only showing relevant variables for this test"
    },
    "execution": {
        "exception_raised": true,
        "exception_type": "ExpressionEvaluationError",
        "result": null
    },
    "validation": {
        "error_handling_correct": true,
        "exception_raised": true,
        "undefined_variable_error": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 15 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        self.assertTrue(test_result["validation"]["exception_raised"], "Exception should be raised")
        self.assertTrue(test_result["validation"]["error_handling_correct"], "Error handling should work")

    def test_nested_recursive_expressions(self):
        """Deep nested recursive expressions"""
        
        # Test data (from original test2.py Test 17)
        variables = {
            'level1': "Start [! level2 !] End",
            'level2': "Middle {! level3 !} Middle", 
            'level3': "Deep [! level4 !] Deep",
            'level4': "Final Value"
        }
        
        # Execute the substitution (deep nested recursion)
        text = "Result: {! level1 !}"
        result = substitute_expressions(text, variables, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "nested_recursive_expressions",
            "template": text,
            "input_variables": variables,
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "result_length": len(result) if isinstance(result, str) else None
            },
            "validation": {
                "expected_value": "Result: Start Middle Deep Final Value Deep Middle End",
                "actual_value": result,
                "values_match": result == "Result: Start Middle Deep Final Value Deep Middle End",
                "is_string": isinstance(result, str),
                "deep_nested_recursion": True,
                "levels_of_nesting": 4
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "nested_recursive_expressions",
    "template": "Result: {! level1 !}",
    "input_variables": {
        "level1": "Start [! level2 !] End",
        "level2": "Middle {! level3 !} Middle",
        "level3": "Deep [! level4 !] Deep",
        "level4": "Final Value"
    },
    "execution": {
        "result": "Result: Start Middle Deep Final Value Deep Middle End",
        "result_length": 53,
        "result_type": "<class 'str'>"
    },
    "validation": {
        "actual_value": "Result: Start Middle Deep Final Value Deep Middle End",
        "deep_nested_recursion": true,
        "expected_value": "Result: Start Middle Deep Final Value Deep Middle End",
        "is_string": true,
        "levels_of_nesting": 4,
        "values_match": true
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 17 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        expected_final = "Result: Start Middle Deep Final Value Deep Middle End"
        self.assertEqual(result, expected_final, "Should handle deep nested recursion correctly")
        self.assertIsInstance(result, str, "Result should be string")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")

    def test_mixed_js_python_recursive(self):
        """Mixed JS/Python recursive expressions"""
        
        # Test data (from original test2.py recursive expressions)
        mixed_vars = {
            'js_var': "JS: {! py_var !}",  # Simple substitution without methods
            'py_var': "python [! final_var !] text",
            'final_var': "FINAL"
        }
        
        # Execute the mixed recursive substitution
        text = "Mixed: [! js_var !]"
        result = substitute_expressions(text, mixed_vars, expected_result_type="python")
        
        # Build comprehensive result for approval
        test_result = {
            "test_name": "mixed_js_python_recursive",
            "template": text,
            "input_variables": mixed_vars,
            "execution": {
                "result": result,
                "result_type": str(type(result)),
                "steps": {
                    "step_1": "final_var -> 'FINAL'",
                    "step_2": "py_var -> 'python [! final_var !] text' -> 'python FINAL text'", 
                    "step_3": "js_var -> 'JS: {! py_var !}' -> 'JS: python FINAL text'",
                    "step_4": "Full template -> 'Mixed: JS: python FINAL text'"
                }
            },
            "validation": {
                "expected_value": "Mixed: JS: python FINAL text",
                "actual_value": result,
                "values_match": result == "Mixed: JS: python FINAL text",
                "is_string": isinstance(result, str),
                "recursive_depth": 3,
                "mixed_syntax": "Both JS {! !} and Python [! !] expressions used"
            },
            "status": "PASSED"
        }
        
        # Approval Test - expected snapshot
        expected_result = """{
    "test_name": "mixed_js_python_recursive",
    "template": "Mixed: [! js_var !]",
    "input_variables": {
        "js_var": "JS: {! py_var !}",
        "py_var": "python [! final_var !] text",
        "final_var": "FINAL"
    },
    "execution": {
        "result": "Mixed: JS: python FINAL text",
        "result_type": "<class 'str'>",
        "steps": {
            "step_1": "final_var -> 'FINAL'",
            "step_2": "py_var -> 'python [! final_var !] text' -> 'python FINAL text'",
            "step_3": "js_var -> 'JS: {! py_var !}' -> 'JS: python FINAL text'",
            "step_4": "Full template -> 'Mixed: JS: python FINAL text'"
        }
    },
    "validation": {
        "expected_value": "Mixed: JS: python FINAL text",
        "actual_value": "Mixed: JS: python FINAL text",
        "values_match": true,
        "is_string": true,
        "recursive_depth": 3,
        "mixed_syntax": "Both JS {! !} and Python [! !] expressions used"
    },
    "status": "PASSED"
}"""
        
        # Convert to JSON for comparison
        result_json = json.dumps(test_result, indent=4, sort_keys=True)
        expected_json = json.dumps(json.loads(expected_result), indent=4, sort_keys=True)
        
        self.assertEqual(result_json, expected_json, 
                        f"Test 18 result doesn't match expected snapshot:\nActual:\n{result_json}\n\nExpected:\n{expected_json}")
        
        # Additional functional assertions
        expected_final = "Mixed: JS: python FINAL text"
        self.assertEqual(result, expected_final, "Should handle mixed JS/Python recursive correctly")
        self.assertTrue(test_result["validation"]["values_match"], "Value validation should pass")
        self.assertTrue(test_result["validation"]["is_string"], "Result should be string")


if __name__ == "__main__":
    unittest.main(verbosity=2)
