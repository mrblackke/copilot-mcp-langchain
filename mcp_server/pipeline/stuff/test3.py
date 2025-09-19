#!/usr/bin/env python3

import sys
import os
sys.path.append('../../../')

from mcp_server.pipeline.expressions import evaluate_expression

def get_test_context():
    """Get test context - all native Python objects"""
    return {
        'users': ['Alice', 'Bob', 'Charlie'],
        'config': {'debug': True, 'timeout': 30},
        'count': 5,
        'message': 'Hello World',
        'is_active': True,
        'data': None,
        'nested': {
            'items': [
                {'name': 'item1', 'value': 10},
                {'name': 'item2', 'value': 20}
            ]
        }
    }

def test_javascript_to_python():
    """Test 1: JavaScript expressions returning Python objects"""
    print("🧪 Test 1: JavaScript {!  !} expressions → Python objects")
    print("-" * 50)
    
    context = get_test_context()
    tests = [
        ("{! users !}", ['Alice', 'Bob', 'Charlie']),
        ("{! users.length !}", 3),  
        ("{! config.debug !}", True),
        ("{! count > 3 !}", True),
        ("{! message + ' - ' + users[0] !}", "Hello World - Alice"),
        ("{! nested.items.map(x => x.value).reduce((a,b) => a+b, 0) !}", 30),
    ]
    
    for expr, expected in tests:
        try:
            result = evaluate_expression(expr, context, "python")
            print(f"  {expr:<50} → {result} ({type(result).__name__})")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"  {expr:<50} → ERROR: {e}")
            raise
    print("✅ PASSED: All JavaScript → Python tests\n")

def test_javascript_to_json():
    """Test 2: JavaScript expressions returning JSON strings"""
    print("🧪 Test 2: JavaScript {!  !} expressions → JSON strings")
    print("-" * 50)
    
    context = get_test_context()
    tests = [
        ("{! users !}", '["Alice", "Bob", "Charlie"]'),
        ("{! users.length !}", '3'),  
        ("{! config.debug !}", 'true'),
        ("{! count > 3 !}", 'true'),
        ("{! message + ' - ' + users[0] !}", '"Hello World - Alice"'),
        ("{! nested.items.map(x => x.value).reduce((a,b) => a+b, 0) !}", '30'),
    ]
    
    for expr, expected in tests:
        try:
            result = evaluate_expression(expr, context, "json") 
            print(f"  {expr:<50} → {result}")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"  {expr:<50} → ERROR: {e}")
            raise
    print("✅ PASSED: All JavaScript → JSON tests\n")

def test_python_to_python():
    """Test 3: Python expressions returning Python objects"""
    print("🧪 Test 3: Python [!  !] expressions → Python objects")
    print("-" * 50)
    
    context = get_test_context()
    tests = [
        ("[! users !]", ['Alice', 'Bob', 'Charlie']),
        ("[! len(users) !]", 3),
        ("[! config['debug'] !]", True), 
        ("[! count > 3 !]", True),
        ("[! message + ' - ' + users[0] !]", "Hello World - Alice"),
        ("[! sum(item['value'] for item in nested['items']) !]", 30),
        ("[! [item['name'] for item in nested['items'] if item['value'] > 15] !]", ['item2']),
    ]
    
    for expr, expected in tests:
        try:
            result = evaluate_expression(expr, context, "python")
            print(f"  {expr:<50} → {result} ({type(result).__name__})")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"  {expr:<50} → ERROR: {e}")
            raise
    print("✅ PASSED: All Python → Python tests\n")

def test_python_to_json():
    """Test 4: Python expressions returning JSON strings"""
    print("🧪 Test 4: Python [!  !] expressions → JSON strings")
    print("-" * 50)
    
    context = get_test_context()
    tests = [
        ("[! users !]", '["Alice", "Bob", "Charlie"]'),
        ("[! len(users) !]", '3'),
        ("[! config['debug'] !]", 'true'), 
        ("[! count > 3 !]", 'true'),
        ("[! message + ' - ' + users[0] !]", '"Hello World - Alice"'),
        ("[! sum(item['value'] for item in nested['items']) !]", '30'),
        ("[! [item['name'] for item in nested['items'] if item['value'] > 15] !]", '["item2"]'),
    ]
    
    for expr, expected in tests:
        try:
            result = evaluate_expression(expr, context, "json")
            print(f"  {expr:<50} → {result}")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"  {expr:<50} → ERROR: {e}")
            raise
    print("✅ PASSED: All Python → JSON tests\n")

def test_fallback_plain_text():
    """Test 5: Fallback for plain text"""
    print("🧪 Test 5: Fallback for plain text")
    print("-" * 50)
    
    context = get_test_context()
    tests = [
        ("plain text", "plain text", '"plain text"'),
        ("no expressions here", "no expressions here", '"no expressions here"'),
        ("just a string", "just a string", '"just a string"')
    ]
    
    for text, expected_py, expected_json in tests:
        result_py = evaluate_expression(text, context, "python")
        result_json = evaluate_expression(text, context, "json")
        print(f"  '{text}' → python: {result_py}, json: {result_json}")
        assert result_py == expected_py, f"Expected python: {expected_py}, got {result_py}"
        assert result_json == expected_json, f"Expected json: {expected_json}, got {result_json}"
    print("✅ PASSED: All Fallback tests\n")


def test_env_variables():
    """Test 6: Built-in environment variables support"""
    print("🧪 Test 6: Built-in env.* variables")
    print("-" * 50)
    
    # Set up test environment variables
    import os
    test_env = {
        'TEST_VAR': 'hello_world',
        'TEST_NUMBER': '42',
        'TEST_PASSWORD': 'secret pass word',  # With spaces
        'TEST_GMAIL_APP_PASSWORD': 'abcd efgh ijkl mnop',  # Gmail style with spaces
    }
    
    # Backup original env vars
    original_env = {}
    for key in test_env:
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = test_env[key]
    
    try:
        context = {}  # Empty context - env should be added automatically
        
        js_tests = [
            ("{! env.TEST_VAR !}", "hello_world"),
            ("{! env.TEST_NUMBER !}", "42"),
            ("{! env.TEST_PASSWORD !}", "secret pass word"),  # Keep spaces as-is
            ("{! env.TEST_GMAIL_APP_PASSWORD !}", "abcd efgh ijkl mnop"),  # Keep spaces as-is
        ]
        
        print("  JavaScript env.* tests:")
        for expr, expected in js_tests:
            try:
                result = evaluate_expression(expr, context, "python")
                print(f"    {expr:<35} → {result}")
                assert result == expected, f"Expected {expected}, got {result}"
            except Exception as e:
                print(f"    {expr:<35} → ERROR: {e}")
                raise
        
        py_tests = [
            ("[! env['TEST_VAR'] !]", "hello_world"),
            ("[! env['TEST_NUMBER'] !]", "42"),
            ("[! env['TEST_PASSWORD'] !]", "secret pass word"),  # Keep spaces as-is
            ("[! env['TEST_GMAIL_APP_PASSWORD'] !]", "abcd efgh ijkl mnop"),  # Keep spaces as-is
        ]
        
        print("  Python env[*] tests:")
        for expr, expected in py_tests:
            try:
                result = evaluate_expression(expr, context, "python")
                print(f"    {expr:<35} → {result}")
                assert result == expected, f"Expected {expected}, got {result}"
            except Exception as e:
                print(f"    {expr:<35} → ERROR: {e}")
                raise
                
        # Test that custom context still works with env
        custom_context = {'custom_var': 'test'}
        result = evaluate_expression("{! custom_var + '_' + env.TEST_VAR !}", custom_context, "python")
        expected = "test_hello_world"
        print(f"    Mixed context test → {result}")
        assert result == expected, f"Expected {expected}, got {result}"
        
    finally:
        # Restore original environment
        for key in test_env:
            if key in original_env:
                os.environ[key] = original_env[key]
            else:
                del os.environ[key]
    
    print("✅ PASSED: All env.* tests\n")


def test_env_password_cleaning():
    """Test 7: Environment password handling (no automatic cleaning)"""
    print("🧪 Test 7: Password handling in environment variables (spaces preserved)")
    print("-" * 50)
    
    import os
    test_passwords = {
        'MY_PASSWORD': 'pass with spaces',
        'GMAIL_APP_PASSWORD': 'abcd efgh ijkl mnop',
        'API_PASSWORD': 'no spaces here',
        'SECRET_PASS': 'multi   word   pass',
        'NORMAL_VAR': 'should not be cleaned',  # Not a password
    }
    
    # Backup and set test vars
    original_env = {}
    for key in test_passwords:
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = test_passwords[key]
    
    try:
        context = {}
        
        tests = [
            ("{! env.MY_PASSWORD !}", "pass with spaces"),  # Keep spaces as-is
            ("{! env.GMAIL_APP_PASSWORD !}", "abcd efgh ijkl mnop"),  # Keep spaces as-is
            ("{! env.API_PASSWORD !}", "no spaces here"),  # Keep spaces as-is
            ("{! env.SECRET_PASS !}", "multi   word   pass"),  # Keep spaces as-is
            ("{! env.NORMAL_VAR !}", "should not be cleaned"),  # Not cleaned
        ]
        
        for expr, expected in tests:
            try:
                result = evaluate_expression(expr, context, "python")
                print(f"  {expr:<30} → {result}")
                assert result == expected, f"Expected '{expected}', got '{result}'"
            except Exception as e:
                print(f"  {expr:<30} → ERROR: {e}")
                raise
                
    finally:
        # Restore original environment
        for key in test_passwords:
            if key in original_env:
                os.environ[key] = original_env[key]
            else:
                del os.environ[key]
    
    print("✅ PASSED: All password cleaning tests\n")

def run_all_tests():
    """Run all expression system tests"""
    import sys
    import os
    sys.path.append('../../../')  # Добавляем корневую папку проекта в sys.path
    
    print("🚀 Expression System Comprehensive Test Suite")
    print("=" * 70)
    
    tests = [
        test_javascript_to_python,
        test_javascript_to_json,
        test_python_to_python,
        test_python_to_json,
        test_fallback_plain_text,
        test_env_variables,
        test_env_password_cleaning
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_func.__name__}: {e}")
            failed += 1
    
    print("=" * 70)
    print(f"📊 Test Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Success Rate: {passed/(passed + failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Expression system is working perfectly! 🚀")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Check output above.")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    import os
    sys.path.append('../../../')  # Добавляем корневую папку проекта в sys.path
    run_all_tests()
