"""Utility functions for JSON to CSV conversion"""

from typing import Any, Dict, List, Union
import json


class JsonUtils:
    """Utility class for JSON operations"""
    
    @staticmethod
    def is_empty(value: Any) -> bool:
        """Check if value is empty (None, empty string, etc.)"""
        return value is None or (isinstance(value, str) and value == "")
    
    @staticmethod
    def safe_str(value: Any) -> str:
        """Safely convert value to string"""
        return str(value) if value is not None else ""
    
    @staticmethod
    def parse_json(json_str: str) -> Union[Dict, List]:
        """Parse JSON string with error handling"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    @staticmethod
    def ensure_list(data: Any) -> List:
        """Ensure data is a list"""
        if isinstance(data, list):
            return data
        else:
            return [data]
