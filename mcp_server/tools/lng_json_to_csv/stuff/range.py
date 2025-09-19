class Range:
    """Python port of Range.java"""
    
    def __init__(self, min_val: int, max_val: int):
        self._min = min_val
        self._max = max_val
    
    def min(self) -> int:
        return self._min
    
    def max(self) -> int:
        return self._max
    
    def next(self):
        self._min = self._max + 1
        self._max = self._min
    
    def set_min(self, value: int):
        self._min = value
    
    def set_max(self, value: int):
        self._max = value
    
    def copy(self):
        return Range(self._min, self._max)
    
    def __str__(self):
        return f"[{self._min}-{self._max}]"
