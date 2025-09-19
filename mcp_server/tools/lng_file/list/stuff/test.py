import unittest
import asyncio
import json
import os
import tempfile
import shutil
from pathlib import Path

# Import the tool under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tools.lng_file.list.tool import run_tool


class TestLngFileListTool(unittest.TestCase):
    """Unit tests for lng_file_list tool using approval testing approach."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create test files and directories structure
        test_files = [
            "README.md",
            "todo.md", 
            "docs/architecture.md",
            "docs/design.md",
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "config.json"
        ]
        
        for file_path in test_files:
            full_path = Path(self.test_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {file_path}\n" * 3)  # Create some content
        
        # Change to test directory
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def run_async_test(self, coro):
        """Helper method to run async tests."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def extract_text_content(self, result):
        """Extract text content from tool result for assertions."""
        if not result:
            return ""
        return result[0].text if hasattr(result[0], 'text') else str(result[0])
    
    def test_should_return_flat_list_when_multiple_patterns(self):
        """Test basic pattern matching with flat list output and deduplication."""
        # given
        parameters = {
            "patterns": ["*.md", "docs/*.md"],
            "base_path": self.test_dir
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        expected_files = {"README.md", "docs\\architecture.md", "docs\\design.md", "todo.md"}
        actual_files = set(actual_output.strip().split('\n'))
        
        self.assertEqual(expected_files, actual_files)
    
    def test_should_group_by_patterns_when_group_by_pattern_true(self):
        """Test pattern grouping when group_by_pattern is enabled."""
        # given
        parameters = {
            "patterns": ["*.md", "docs/*.md"],
            "base_path": self.test_dir,
            "group_by_pattern": True
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        # Check that grouping structure is correct
        self.assertIn("# Pattern: *.md", actual_output)
        self.assertIn("# Pattern: docs/*.md", actual_output)
        self.assertIn("README.md", actual_output)
        self.assertIn("todo.md", actual_output)
        self.assertIn("docs\\architecture.md", actual_output)
        self.assertIn("docs\\design.md", actual_output)
    
    def test_should_return_json_format_when_output_format_json(self):
        """Test JSON output format with metadata."""
        # given
        parameters = {
            "patterns": ["*.md"],
            "base_path": self.test_dir,
            "output_format": "json"
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        # Parse JSON to verify structure and key fields
        json_result = json.loads(actual_output)
        
        # Assert structure
        self.assertIn("items", json_result)
        self.assertIn("metadata", json_result)
        
        # Assert metadata fields
        metadata = json_result["metadata"]
        self.assertEqual("file_list_patterns", metadata["operation"])
        self.assertEqual(["*.md"], metadata["patterns"])
        self.assertTrue(metadata["success"])
        self.assertEqual(2, metadata["total_items"])  # README.md, todo.md
        
        # Assert items structure
        items = json_result["items"]
        self.assertEqual(2, len(items))
        
        # Check first item structure
        item = items[0]
        expected_fields = ["path", "name", "type", "pattern", "size", "modified_time", 
                          "permissions", "is_hidden", "absolute_path"]
        for field in expected_fields:
            self.assertIn(field, item)
        
        # Check sorted order and expected files
        file_names = [item["name"] for item in items]
        self.assertEqual(["README.md", "todo.md"], file_names)
    
    def test_should_return_detailed_format_when_output_format_detailed(self):
        """Test detailed output format with file information."""
        # given
        parameters = {
            "patterns": ["**/*.py"],
            "base_path": self.test_dir,
            "output_format": "detailed"
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        # Verify detailed format structure
        lines = actual_output.strip().split('\n')
        self.assertTrue(lines[0].startswith("Multi-pattern file listing:"))
        self.assertTrue(lines[1].startswith("Patterns: **/*.py"))
        self.assertTrue(lines[2].startswith("Total items:"))
        
        # Should contain Python files
        self.assertIn("src\\main.py", actual_output)
        self.assertIn("src\\utils.py", actual_output) 
        self.assertIn("tests\\test_main.py", actual_output)
        
        # Should contain byte information
        self.assertIn("bytes)", actual_output)
    
    def test_should_include_empty_results_when_pattern_matches_nothing(self):
        """Test empty patterns are included in grouping output."""
        # given
        parameters = {
            "patterns": ["*.txt", "*.nonexistent", "*.md"],
            "base_path": self.test_dir,
            "group_by_pattern": True
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        expected_patterns = ["# Pattern: *.txt", "# Pattern: *.nonexistent", "# Pattern: *.md"]
        for pattern in expected_patterns:
            self.assertIn(pattern, actual_output)
        
        # *.txt and *.nonexistent should be empty, *.md should have files
        self.assertIn("README.md", actual_output)
        self.assertIn("todo.md", actual_output)
    
    def test_should_return_error_when_patterns_empty(self):
        """Test validation error when patterns array is empty."""
        # given
        parameters = {
            "patterns": [],
            "base_path": self.test_dir
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        json_result = json.loads(actual_output)
        self.assertIn("metadata", json_result)
        self.assertFalse(json_result["metadata"]["success"])
        self.assertIn("patterns parameter is required and must be a non-empty list", 
                     json_result["metadata"]["error"])
    
    def test_should_return_error_when_base_path_not_exists(self):
        """Test validation error when base_path does not exist."""
        # given
        parameters = {
            "patterns": ["*.md"],
            "base_path": "/nonexistent/path/that/does/not/exist"
        }
        
        # when
        result = self.run_async_test(run_tool("lng_file_list", parameters))
        actual_output = self.extract_text_content(result)
        
        # then
        json_result = json.loads(actual_output)
        self.assertIn("metadata", json_result)
        self.assertFalse(json_result["metadata"]["success"])
        self.assertIn("Base path not found", json_result["metadata"]["error"])


if __name__ == '__main__':
    unittest.main()
