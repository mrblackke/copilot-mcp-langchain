"""Python port of Matrix.java"""

from typing import List, Optional, Tuple
from collections import deque


class Matrix:
    """Python port of Matrix.java"""
    
    EMPTY = None
    SEPARATOR = "==>"
    
    def __init__(self):
        self.data: List[deque] = []
        self.current_header = 0
        self.header_size = 1
        self.current_line = 0
        self.base_line = 0
        self._new_line_flag = False
    
    def insert_row(self, row_index: int):
        """Insert a new row at the specified index"""
        new_row = deque()
        if not self.data:
            self.data.append(new_row)
            return
        
        # Fill new row with empty values to match existing columns
        for i in range(len(self.data[0]) if self.data else 0):
            new_row.append(self.EMPTY)
        self.data.insert(row_index, new_row)
    
    def insert_column(self, col_index: int):
        """Insert a new column at the specified index"""
        for row in self.data:
            row.insert(col_index, self.EMPTY)
    
    def get_or_create_header(self, key: str) -> int:
        """Get existing header or create new one, returns column index - exact port of Java getOrCreateHeader"""
        if len(self.data) <= self.current_header:
            self.insert_row(self.current_header)
            self.current_line += 1
            self.base_line += 1
        
        header = self.data[self.current_header]
        
        # Check if key already exists in current header
        for i in range(len(header)):
            if key == header[i]:
                return i
        
        # If this is the first header level, just append
        if self.current_header == 0:
            self.insert_column(len(header))
            header[len(header) - 1] = key
            return len(header) - 1
        
        # For nested headers - exact port of Java logic
        parent_key = key[:key.rfind(".")]
        
        parent_pos = -1
        parent_header = self.data[self.current_header - 1]
        for i in range(len(parent_header)):
            if parent_header[i] == parent_key:  # Objects.equals equivalent
                parent_pos = i
                break
        
        if parent_pos == -1:
            raise ValueError(f"Parent key not found: {parent_key}")
        
        # If parent position is empty in current header, use it
        if self._is_empty(header[parent_pos]):
            header[parent_pos] = key
            return parent_pos
        
        # Complex positioning logic - exact port from Java do-while loop
        new_pos = parent_pos
        insert_before_other_category = False
        
        while True:
            value = header[new_pos] if new_pos < len(header) else None
            
            if value is not None and not value.startswith(parent_key):
                insert_before_other_category = True
                break
                
            all_children_is_empty = self._check_all_children_in_header(self.current_header + 1, new_pos)
            new_pos += 1
            
            # Exit condition from Java do-while loop
            if not ((not self._is_empty(value) or not all_children_is_empty) and new_pos < len(header)):
                break
        
        if not insert_before_other_category and new_pos != len(header):
            new_pos -= 1
            
        self.insert_column(new_pos)
        header[new_pos] = key
        return new_pos
    
    def _check_all_children_in_header(self, from_y: int, x: int) -> bool:
        """Check if all children in header are empty"""
        for y in range(from_y, self.header_size):
            if y < len(self.data):
                row = self.data[y]
                if x < len(row) and not self._is_empty(row[x]):
                    return False
        return True
    
    def set(self, y: int, x: int, value: str):
        """Set value at specific position"""
        self.data[y][x] = value
    
    def to_string(self,
                  column_delimiter: str,
                  cell_left_delimiter: Optional[str],
                  cell_right_delimiter: Optional[str],
                  line_chars_need_to_be_escaped_with_cell_delimiter: Optional[str],
                  header_delimiter: Optional[str],
                  line_replacements: Optional[List[str]],
                  padding_to_max_cell_length: bool) -> str:
        """Convert matrix to string format - exact port of Java toString method"""
        
        # Process replacements
        replacements = None
        if line_replacements:
            replacements = []
            for replacement in line_replacements:
                parts = replacement.split(self.SEPARATOR)
                replacements.append((parts[0], parts[1]))
        
        sb = []
        header_delimiter_pos = 0
        max_line_length = 0
        
        for y in range(len(self.data)):
            row = self.data[y]
            line_length = 0
            line_parts = []
            
            for x in range(len(row)):
                value = row[x] if row[x] is not None else ""
                
                # Check if escaping is needed
                escape = False
                if line_chars_need_to_be_escaped_with_cell_delimiter:
                    escape = self._contains_any(value, line_chars_need_to_be_escaped_with_cell_delimiter)
                
                # Apply replacements
                if replacements:
                    for old, new in replacements:
                        value = value.replace(old, new)
                
                # Build cell value with delimiters
                cell_content = ""
                if cell_left_delimiter and escape:
                    cell_content += cell_left_delimiter
                    line_length += len(cell_left_delimiter)
                
                cell_content += value
                line_length += len(value)
                
                if cell_right_delimiter and escape:
                    cell_content += cell_right_delimiter
                    line_length += len(cell_right_delimiter)
                
                # Add padding if required
                if padding_to_max_cell_length:
                    max_length = self._get_max_cell_length(x)
                    padding = max_length - len(value)
                    cell_content += " " * padding
                    line_length += padding
                
                line_parts.append(cell_content)
                
                if x < len(row) - 1:
                    line_length += len(column_delimiter)
            
            max_line_length = max(max_line_length, line_length)
            sb.append(column_delimiter.join(line_parts))
            
            if y == self.header_size - 1:
                header_delimiter_pos = len(sb)
        
        # Insert header delimiter if specified
        if header_delimiter:
            header_line = header_delimiter * max_line_length
            header_line = header_line[:max_line_length]
            sb.insert(header_delimiter_pos, header_line)
        
        # Java StringBuilder appends \n after EVERY line including the last one
        # Each line gets its own \n at the end
        result = "\n".join(sb)
        if result:  # Add final newline only if there's content
            result += "\n"
        return result
    
    def _contains_any(self, value: str, chars: str) -> bool:
        """Check if value contains any of the specified characters"""
        for c in value:
            if c in chars:
                return True
        return False
    
    def _get_max_cell_length(self, x: int) -> int:
        """Get maximum cell length in column x"""
        max_length = 0
        for row in self.data:
            if x < len(row):
                value = row[x]
                max_length = max(max_length, len(value) if value is not None else 0)
        return max_length
    
    def child_header(self):
        """Move to child header level"""
        self.current_header += 1
        if self.current_header == self.header_size:
            self.insert_row(self.header_size)
            self.header_size += 1
            self.base_line += 1
            self.current_line += 1
    
    def parent_header(self):
        """Move back to parent header level"""
        self.current_header -= 1
        if self.current_header < 0:
            self.current_header = 0
    
    def inject(self, x: int, same_line: bool, value: str):
        """Inject value at position"""
        if self._new_line_flag:
            self.base_line = len(self.data)
            self.current_line = self.base_line - 1
            self._new_line_flag = False
        
        if same_line:
            if len(self.data) <= self.base_line:
                self.insert_row(self.base_line)
            if x < len(self.data[self.base_line]) and self.data[self.base_line][x] is None:
                self.current_line = self.base_line
        else:
            self.current_line += 1
            if self.current_line >= len(self.data):
                self.insert_row(len(self.data))
        
        # Ensure row has enough columns
        while x >= len(self.data[self.current_line]):
            self.data[self.current_line].append(self.EMPTY)
        
        self.set(self.current_line, x, str(value))
    
    def remove_headers_duplicates(self):
        """Remove duplicate header prefixes"""
        for y in range(self.header_size):
            row = self.data[y]
            for x in range(len(row)):
                value = row[x]
                if self._is_empty(value):
                    continue
                
                value_prefix = value + "."
                for yy in range(y + 1, self.header_size):
                    if yy < len(self.data):
                        next_row = self.data[yy]
                        for xx in range(len(row)):
                            if xx < len(next_row):
                                value2 = next_row[xx]
                                if value2 is not None and value2.startswith(value_prefix):
                                    next_row[xx] = value2[len(value_prefix):]
    
    def new_line(self):
        """Mark that next injection should create a new line"""
        self._new_line_flag = True
    
    def _is_empty(self, value) -> bool:
        """Check if value is empty"""
        return value is None or value == ""
