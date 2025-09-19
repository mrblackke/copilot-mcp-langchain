"""
File-based State Manager for MCP Server Tools

This module provides a file-based state storage mechanism for tools in the MCP server.
The state is stored in files on the filesystem within a specified directory.
"""

import os
import json
from pathlib import Path
from typing import Any, Optional, Dict


class FileStateManager:
    """
    A file-based state manager that stores data in files within a specified directory.
    """
    
    def __init__(self, base_path: str):
        """
        Initialize the FileStateManager with a base directory path.
        
        Args:
            base_path: Relative path to the directory where files will be stored
        """
        self.base_path = Path(base_path)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Create the base directory if it doesn't exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str, extension: str = ".txt") -> Path:
        """
        Get the full file path for a given key.
        
        Args:
            key: The key/filename
            extension: File extension to use
            
        Returns:
            Path object for the file
        """
        return self.base_path / f"{key}{extension}"
    
    def get(self, key: str, default: Any = None, extension: str = ".txt") -> Any:
        """
        Get a value from a file by key.
        
        Args:
            key: The key/filename to look up
            default: The default value to return if file is not found
            extension: File extension to use
            
        Returns:
            The content of the file, or the default value if not found
        """
        file_path = self._get_file_path(key, extension)
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if extension == ".json":
                    return json.load(f)
                else:
                    return f.read()
        except Exception:
            return default
    
    def set(self, key: str, value: Any, extension: str = ".txt") -> Any:
        """
        Set a value in a file.
        
        Args:
            key: The key/filename to store the value under
            value: The value to store
            extension: File extension to use
            
        Returns:
            The value that was stored
        """
        file_path = self._get_file_path(key, extension)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if extension == ".json":
                    json.dump(value, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(value))
            return value
        except Exception as e:
            raise Exception(f"Failed to write file {file_path}: {str(e)}")
    
    def delete(self, key: str, extension: str = ".txt") -> bool:
        """
        Delete a file by key.
        
        Args:
            key: The key/filename to delete
            extension: File extension to use
            
        Returns:
            True if the file was deleted, False if it didn't exist
        """
        file_path = self._get_file_path(key, extension)
        
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False
        return False
    
    def has(self, key: str, extension: str = ".txt") -> bool:
        """
        Check if a file exists for the given key.
        
        Args:
            key: The key/filename to check
            extension: File extension to use
            
        Returns:
            True if the file exists, False otherwise
        """
        file_path = self._get_file_path(key, extension)
        return file_path.exists()
    
    def list_files(self, extension: str = ".txt") -> list[str]:
        """
        List all files with the given extension in the directory.
        
        Args:
            extension: File extension to filter by
            
        Returns:
            List of filenames (without extension)
        """
        try:
            files = []
            for file_path in self.base_path.glob(f"*{extension}"):
                if file_path.is_file():
                    files.append(file_path.stem)
            return sorted(files)
        except Exception:
            return []
    
    def get_all(self, extension: str = ".txt") -> Dict[str, Any]:
        """
        Get all files with the given extension as a dictionary.
        
        Args:
            extension: File extension to filter by
            
        Returns:
            Dictionary with filename (without extension) as key and file content as value
        """
        result = {}
        for filename in self.list_files(extension):
            result[filename] = self.get(filename, extension=extension)
        return result
    
    def clear(self, extension: str = ".txt"):
        """
        Delete all files with the given extension in the directory.
        
        Args:
            extension: File extension to filter by
        """
        try:
            for file_path in self.base_path.glob(f"*{extension}"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception:
            pass


# Create a global instance for prompts
prompts_manager = FileStateManager("mcp_server/config/prompt")
