#!/usr/bin/env python3
"""
Comprehensive test script for lng_file tools (read, write, list)
Tests all functionality including edge cases, encodings, and error handling
"""

import sys
import os
import tempfile
import json

# Add the parent directory to sys.path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from read.tool import run_tool as read_tool
from write.tool import run_tool as write_tool
from list.tool import run_tool as list_tool

def print_test_result(test_name, result, expected_success=True):
    """Helper function to print test results consistently"""
    print(f"\n{test_name}")
    print("-" * 60)
    
    # Try to parse as JSON to check if it's structured
    try:
        parsed = json.loads(result[0].text)
        if "metadata" in parsed:
            success = parsed["metadata"].get("success", False)
            if success == expected_success:
                print("✅ PASS")
            else:
                print("❌ FAIL")
        else:
            # Plain text result
            if expected_success:
                print("✅ PASS (Plain text)")
            else:
                print("❌ FAIL (Expected error but got plain text)")
    except json.JSONDecodeError:
        # Not JSON, check if it's expected plain text
        if expected_success and not result[0].text.startswith("{"):
            print("✅ PASS (Plain text)")
        else:
            print("❌ FAIL (JSON parsing error)")
    
    print(f"Result: {result[0].text[:200]}{'...' if len(result[0].text) > 200 else ''}")

async def test_file_operations():
    """Comprehensive test suite for both read and write operations"""
    
    print("🧪 COMPREHENSIVE TESTING SUITE FOR LNG_FILE TOOLS")
    print("=" * 80)
    
    # Create temporary directory for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test_file.txt")
        unicode_file = os.path.join(temp_dir, "unicode_test.txt")
        nested_file = os.path.join(temp_dir, "nested", "deep", "file.txt")
        
        print(f"\n📁 Testing in temporary directory: {temp_dir}")
        
        print("\n" + "=" * 80)
        print("🔧 TESTING lng_file_write")
        print("=" * 80)
        
        # Test 1: Create new file
        result = await write_tool("lng_file_write", {
            "file_path": test_file,
            "content": "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n",
            "mode": "create"
        })
        print_test_result("Test 1: Creating new file", result, True)
        
        # Test 2: Try to create existing file (should fail)
        result = await write_tool("lng_file_write", {
            "file_path": test_file,
            "content": "This should fail",
            "mode": "create"
        })
        print_test_result("Test 2: Creating existing file (should fail)", result, False)
        
        # Test 3: Append to existing file
        result = await write_tool("lng_file_write", {
            "file_path": test_file,
            "content": "Line 6\nLine 7\n",
            "mode": "append"
        })
        print_test_result("Test 3: Appending to existing file", result, True)
        
        # Test 4: Overwrite existing file
        result = await write_tool("lng_file_write", {
            "file_path": test_file,
            "content": "Overwritten content\nLine 2 of overwrite\n",
            "mode": "overwrite"
        })
        print_test_result("Test 4: Overwriting existing file", result, True)
        
        # Test 5: Create file with nested directories (auto-create)
        result = await write_tool("lng_file_write", {
            "file_path": nested_file,
            "content": "File in nested directory\nCreated automatically\n"
        })
        print_test_result("Test 5: Creating file with auto-directory creation", result, True)
        
        # Test 6: Create Unicode file
        result = await write_tool("lng_file_write", {
            "file_path": unicode_file,
            "content": "Unicode test: 🌍 Hello! Русский текст. 中文字符. émojis 🎉",
            "encoding": "utf-8"
        })
        print_test_result("Test 6: Creating Unicode file", result, True)
        
        # Test 7: Empty file creation
        empty_file = os.path.join(temp_dir, "empty.txt")
        result = await write_tool("lng_file_write", {
            "file_path": empty_file,
            "content": ""
        })
        print_test_result("Test 7: Creating empty file", result, True)
        
        # Test 8: Test error - missing file path
        result = await write_tool("lng_file_write", {
            "content": "Should fail without file_path"
        })
        print_test_result("Test 8: Missing file_path parameter (should fail)", result, False)
        
        # Test 9: Test error - missing content parameter
        result = await write_tool("lng_file_write", {
            "file_path": os.path.join(temp_dir, "no_content.txt")
        })
        print_test_result("Test 9: Missing content parameter (should fail)", result, False)
        
        print("\n" + "=" * 80)
        print("📖 TESTING lng_file_read")
        print("=" * 80)
        
        # Test 10: Read entire file (plain text format - default)
        result = await read_tool("lng_file_read", {
            "file_path": test_file
        })
        print_test_result("Test 10: Reading file (plain text format)", result, True)
        
        # Test 11: Read with JSON format
        result = await read_tool("lng_file_read", {
            "file_path": test_file,
            "output_format": "json"
        })
        print_test_result("Test 11: Reading file (JSON format)", result, True)
        
        # Test 12: Read with offset and limit (plain text)
        result = await read_tool("lng_file_read", {
            "file_path": test_file,
            "offset": 1,
            "limit": 1
        })
        print_test_result("Test 12: Reading with offset/limit (plain text)", result, True)
        
        # Test 13: Read with offset and limit (JSON format)
        result = await read_tool("lng_file_read", {
            "file_path": test_file,
            "offset": 0,
            "limit": 2,
            "output_format": "json"
        })
        print_test_result("Test 13: Reading with offset/limit (JSON format)", result, True)
        
        # Test 14: Read Unicode file
        result = await read_tool("lng_file_read", {
            "file_path": unicode_file,
            "encoding": "utf-8"
        })
        print_test_result("Test 14: Reading Unicode file", result, True)
        
        # Test 15: Read empty file
        result = await read_tool("lng_file_read", {
            "file_path": empty_file
        })
        print_test_result("Test 15: Reading empty file", result, True)
        
        # Test 16: Read nested file
        result = await read_tool("lng_file_read", {
            "file_path": nested_file,
            "output_format": "json"
        })
        print_test_result("Test 16: Reading nested directory file", result, True)
        
        # Test 17: Test error - non-existent file (plain text mode)
        result = await read_tool("lng_file_read", {
            "file_path": os.path.join(temp_dir, "nonexistent.txt")
        })
        print_test_result("Test 17: Non-existent file (plain text mode, returns JSON)", result, False)
        
        # Test 18: Test error - non-existent file (JSON mode)
        result = await read_tool("lng_file_read", {
            "file_path": os.path.join(temp_dir, "nonexistent2.txt"),
            "output_format": "json"
        })
        print_test_result("Test 18: Non-existent file (JSON mode)", result, False)
        
        # Test 19: Test error - missing file path
        result = await read_tool("lng_file_read", {
            "offset": 0
        })
        print_test_result("Test 19: Missing file_path parameter (should fail)", result, False)
        
        # Test 20: Test offset beyond file length
        result = await read_tool("lng_file_read", {
            "file_path": test_file,
            "offset": 1000,
            "output_format": "json"
        })
        print_test_result("Test 20: Offset beyond file length", result, True)
        
        print("\n" + "=" * 80)
        print("🔄 INTEGRATION TESTS")
        print("=" * 80)
        
        # Test 21: Write then read cycle
        cycle_file = os.path.join(temp_dir, "cycle_test.txt")
        write_result = await write_tool("lng_file_write", {
            "file_path": cycle_file,
            "content": "Write-Read cycle test\nMultiple lines for testing\nThird line here\n"
        })
        
        read_result = await read_tool("lng_file_read", {
            "file_path": cycle_file,
            "offset": 1,
            "limit": 1
        })
        print_test_result("Test 21: Write-Read cycle test", read_result, True)
        
        # Test 22: Multiple operations on same file
        multi_file = os.path.join(temp_dir, "multi_ops.txt")
        
        # Create
        await write_tool("lng_file_write", {
            "file_path": multi_file,
            "content": "Initial content\n"
        })
        
        # Append
        await write_tool("lng_file_write", {
            "file_path": multi_file,
            "content": "Appended line 1\n",
            "mode": "append"
        })
        
        # Read and verify
        final_result = await read_tool("lng_file_read", {
            "file_path": multi_file,
            "output_format": "json"
        })
        print_test_result("Test 22: Multiple operations on same file", final_result, True)
        
        print("\n" + "=" * 80)
        print("📁 TESTING lng_file_list")
        print("=" * 80)
        
        # Create test directory structure for listing tests
        subdir1 = os.path.join(temp_dir, "subdir1")
        subdir2 = os.path.join(temp_dir, "subdir2")
        hidden_dir = os.path.join(temp_dir, ".hidden")
        os.makedirs(subdir1, exist_ok=True)
        os.makedirs(subdir2, exist_ok=True)
        os.makedirs(hidden_dir, exist_ok=True)
        
        # Create various test files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("test content 1")
        with open(os.path.join(temp_dir, "file2.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(temp_dir, ".hidden_file"), "w") as f:
            f.write("hidden content")
        with open(os.path.join(subdir1, "nested.txt"), "w") as f:
            f.write("nested file")
        with open(os.path.join(subdir2, "another.py"), "w") as f:
            f.write("another python file")
        with open(os.path.join(hidden_dir, "hidden_nested.txt"), "w") as f:
            f.write("hidden nested content")
        
        # Test 23: Basic pattern listing (simple format)
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir
        })
        print_test_result("Test 23: Basic pattern listing (simple format)", result, True)
        
        # Test 24: Pattern listing with absolute paths
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir,
            "path_type": "absolute"
        })
        print_test_result("Test 24: Pattern listing with absolute paths", result, True)
        
        # Test 25: List only files (exclude directories)
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir,
            "include_directories": False
        })
        print_test_result("Test 25: List only files", result, True)
        
        # Test 26: List only directories (exclude files)
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir,
            "include_files": False
        })
        print_test_result("Test 26: List only directories", result, True)
        
        # Test 27: Recursive listing
        result = await list_tool("lng_file_list", {
            "patterns": ["**/*"],
            "base_path": temp_dir
        })
        print_test_result("Test 27: Recursive pattern listing", result, True)
        
        # Test 28: Pattern filtering (*.py files recursive)
        result = await list_tool("lng_file_list", {
            "patterns": ["**/*.py"],
            "base_path": temp_dir
        })
        print_test_result("Test 28: Pattern filtering (*.py files)", result, True)
        
        # Test 29: Pattern filtering (*.txt files) with absolute paths
        result = await list_tool("lng_file_list", {
            "patterns": ["**/*.txt"],
            "base_path": temp_dir,
            "path_type": "absolute"
        })
        print_test_result("Test 29: Pattern filtering (*.txt) with absolute paths", result, True)
        
        # Test 30: Include hidden files with multiple patterns
        result = await list_tool("lng_file_list", {
            "patterns": ["*", ".*"],
            "base_path": temp_dir,
            "show_hidden": True
        })
        print_test_result("Test 30: Include hidden files", result, True)
        
        # Test 31: Detailed output format
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir,
            "output_format": "detailed"
        })
        print_test_result("Test 31: Detailed output format", result, True)
        
        # Test 32: JSON output format
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": temp_dir,
            "output_format": "json"
        })
        print_test_result("Test 32: JSON output format", result, True)
        
        # Test 33: Multiple patterns with grouping and JSON format
        result = await list_tool("lng_file_list", {
            "patterns": ["**/*.py", "**/*.txt", "**/.*"],
            "base_path": temp_dir,
            "group_by_pattern": True,
            "show_hidden": True,
            "output_format": "json"
        })
        print_test_result("Test 33: Multiple patterns with grouping (JSON format)", result, True)
        
        # Test 34: Test error - non-existent base_path
        result = await list_tool("lng_file_list", {
            "patterns": ["*"],
            "base_path": os.path.join(temp_dir, "nonexistent_dir")
        })
        print_test_result("Test 34: Non-existent base_path (should fail)", result, False)
        
        # Test 35: Test error - empty patterns array
        result = await list_tool("lng_file_list", {
            "patterns": [],
            "base_path": temp_dir
        })
        print_test_result("Test 35: Empty patterns array (should fail)", result, False)
        
        # Test 36: Test error - missing patterns parameter
        result = await list_tool("lng_file_list", {
            "base_path": temp_dir
        })
        print_test_result("Test 36: Missing patterns parameter (should fail)", result, False)
        
        # Test 37: Complex combination - multiple patterns with detailed output
        result = await list_tool("lng_file_list", {
            "patterns": ["**/*.txt", "**/*.py", "**/.*"],
            "base_path": temp_dir,
            "show_hidden": True,
            "output_format": "detailed",
            "path_type": "absolute"
        })
        print_test_result("Test 37: Complex combination test", result, True)
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print("✅ All tests completed!")
        print("📝 Check individual test results above for pass/fail status")
        print(f"🗂️  Temporary test directory: {temp_dir}")
        print("🔍 For detailed analysis, review the JSON outputs and error messages")
        print("\n🧪 Total tests run:")
        print("   • lng_file_write: 9 tests")
        print("   • lng_file_read: 11 tests") 
        print("   • lng_file_list: 15 tests")
        print("   • Integration: 2 tests")
        print("   📈 Total: 37 tests")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_file_operations())
