"""Python port of JsonToCsv.java"""

import json
from typing import List, Optional, Any, Dict, Union
from matrix import Matrix


class JsonToCsv:
    """Python port of JsonToCsv.java"""
    
    DEBUG = False
    
    @staticmethod
    def json_to_csv(json_str: str) -> str:
        """Convert JSON to CSV with default parameters"""
        return JsonToCsv._json_to_csv(
            json_str,
            ",",
            '"',
            '"',
            '\n",',
            None,
            ['"' + Matrix.SEPARATOR + '""'],
            False,
            True
        )
    
    @staticmethod
    def json_to_markdown(json_str: str) -> str:
        """Convert JSON to Markdown table format"""
        return JsonToCsv._json_to_csv(
            json_str,
            "|",
            None,
            None,
            None,
            "-",
            None,
            True,
            True
        )
    
    @staticmethod
    def _json_to_csv(
        json_str: str,
        column_delimiter: str,
        cell_left_delimiter: Optional[str],
        cell_right_delimiter: Optional[str],
        line_chars_need_to_be_escaped_with_cell_delimiter: Optional[str],
        header_delimiter: Optional[str],
        line_replacements: Optional[List[str]],
        padding_to_max_cell_length: bool,
        remove_headers_duplicates: bool
    ) -> str:
        """Internal method to convert JSON to CSV/Markdown"""
        
        # Parse JSON data
        data = json.loads(json_str)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        matrix = Matrix()
        
        # Process each element in the data
        JsonToCsv._process_element(matrix, data, "", False, 0)
        
        # Remove header duplicates if requested
        if remove_headers_duplicates:
            matrix.remove_headers_duplicates()
        
        # Convert matrix to string
        return matrix.to_string(
            column_delimiter,
            cell_left_delimiter,
            cell_right_delimiter,
            line_chars_need_to_be_escaped_with_cell_delimiter,
            header_delimiter,
            line_replacements,
            padding_to_max_cell_length
        )
    
    @staticmethod
    @staticmethod
    def _process_element(matrix: Matrix, obj: Any, prefix: str, same_line: bool, depth: int):
        """Process individual elements recursively"""
        x = 0
        if prefix:
            x = matrix.get_or_create_header(prefix)
        
        if isinstance(obj, dict):
            # Handle dictionary/object
            if depth > 1:
                matrix.child_header()
            
            # Use original dict order (insertion order in Python 3.7+)
            for key, value in obj.items():
                new_key = key if not prefix else f"{prefix}.{key}"
                JsonToCsv._process_element(matrix, value, new_key, same_line, depth + 1)
                same_line = True
            
            if depth > 1:
                matrix.parent_header()
        
        elif isinstance(obj, list):
            # Handle array/list
            for i, item in enumerate(obj):
                if depth == 0:
                    matrix.new_line()
                else:
                    same_line = i == 0
                
                JsonToCsv._process_element(matrix, item, prefix, same_line, depth + 1)
        
        else:
            # Handle primitive values
            # Convert boolean values to lowercase like Java
            if isinstance(obj, bool):
                value = "true" if obj else "false"
            else:
                value = str(obj)
            matrix.inject(x, same_line, value)
            
            if JsonToCsv.DEBUG:
                print(f"Injecting: {prefix} -> {obj}")
                print("=" * 80)
                print(matrix.to_string("|", None, None, None, "-", None, True))
                print("=" * 80)
                print(matrix.to_string("|", None, None, None, "-", None, True))
                print("=" * 80)
