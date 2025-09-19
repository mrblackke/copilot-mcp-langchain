"""
Expression evaluation strategies for pipeline execution.

Provides unified expression evaluation with multiple backends:
- JavaScript expressions: {! expression !}  
- Python expressions: [! expression !]

Context always contains native Python objects (dict, list, str, int, bool, None).
Results can be returned as Python objects or JSON strings based on expected_result_type.

Built-in variables:
- env.*: Access to environment variables (env.HOME, env.PATH, etc.)
"""

import json
import re
import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger('mcp_server.pipeline.expressions')

# Check for PyMiniRacer availability
try:
    import py_mini_racer
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False
    logger.warning("PyMiniRacer not available. JavaScript expressions will use fallback Python evaluation.")


def build_default_context(custom_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build default expression context with built-in variables."""
    context = {
        "env": dict(os.environ),
    }
    
    # Add custom context
    if custom_context:
        context.update(custom_context)
    
    return context


class ExpressionEvaluationError(Exception):
    """Raised when expression evaluation fails."""
    
    def __init__(self, strategy_name: str, expression: str, step_info: Dict[str, Any], original_error: Exception):
        self.strategy_name = strategy_name
        self.expression = expression
        self.step_info = step_info
        self.original_error = original_error
        
        super().__init__(
            f"Expression evaluation failed in '{strategy_name}' at step '{step_info.get('step', 'unknown')}': "
            f"'{expression}' -> '{str(original_error)}'"
        )


class ExpressionStrategy(ABC):
    """Base class for expression evaluation strategies."""
    
    @abstractmethod
    def can_handle(self, expression: str) -> bool:
        """Check if this strategy can handle the given expression."""
        pass
    
    @abstractmethod
    def evaluate(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any] = None) -> Any:
        """
        Evaluate expression with given context.
        
        Args:
            expression: Expression string (e.g., "{! variable !}" or "[! expression !]")
            context: Dictionary of native Python objects
            expected_result_type: "python" or "json"
            step_info: Information about current pipeline step for error reporting
            
        Returns:
            Result in format specified by expected_result_type
        """
        pass
    
    def extract_expression(self, expression: str) -> str:
        """Extract clean expression content from wrapper syntax."""
        # Remove {! ... !} or [! ... !] wrapper
        if expression.startswith('{! ') and expression.endswith(' !}'):
            return expression[3:-3]
        elif expression.startswith('[! ') and expression.endswith(' !]'):
            return expression[3:-3]
        return expression
    
    def format_result(self, result: Any, expected_result_type: str) -> Any:
        """Format result according to expected type."""
        if expected_result_type == "python":
            return result
        elif expected_result_type == "json":
            try:
                return json.dumps(result, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize result to JSON: {e}, returning string representation")
                return str(result)
        else:
            raise ValueError(f"Unknown expected_result_type: {expected_result_type}")


class JavaScriptExpressionStrategy(ExpressionStrategy):
    """Strategy for evaluating JavaScript expressions: {! expression !}"""
    
    def __init__(self):
        self.js_context = None
        if JS_AVAILABLE:
            self.js_context = py_mini_racer.MiniRacer()
    
    def can_handle(self, expression: str) -> bool:
        """Check if expression uses JavaScript syntax: {! ... !}"""
        # Must be exactly a single pure JavaScript expression
        expression = expression.strip()
        if not (expression.startswith('{! ') and expression.endswith(' !}') and len(expression) > 6):
            return False
        
        # Count occurrences to ensure it's a single pure expression
        return expression.count('{!') == 1 and expression.count('!}') == 1
    
    def evaluate(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any] = None) -> Any:
        """Evaluate JavaScript expression."""
        step_info = step_info or {}
        
        try:
            if not JS_AVAILABLE:
                return self._evaluate_fallback(expression, context, expected_result_type, step_info)
            
            clean_expression = self.extract_expression(expression)
            # logger.debug(f"JS: Clean expression: {clean_expression}")
            
            # Set context variables in JavaScript environment
            self._set_js_context(context)
            
            # Evaluate expression in JavaScript
            js_result = self.js_context.eval(clean_expression)
            # logger.debug(f"JS: Raw JS result: {js_result!r} type: {type(js_result)}")
            
            # Convert JavaScript result back to Python
            python_result = self._convert_js_to_python(js_result, clean_expression)
            # logger.debug(f"JS: Python result: {python_result!r} type: {type(python_result)}")
            
            # Format result
            final_result = self.format_result(python_result, expected_result_type)
            # logger.debug(f"JS: Final result: {final_result!r} type: {type(final_result)}, expected_type: {expected_result_type}")
            
            return final_result
            
        except Exception as e:
            raise ExpressionEvaluationError(
                strategy_name="JavaScript",
                expression=expression,
                step_info=step_info,
                original_error=e
            )
    
    def _set_js_context(self, context: Dict[str, Any]) -> None:
        """Set Python context variables in JavaScript environment."""
        for key, value in context.items():
            try:
                if isinstance(value, (dict, list)):
                    js_value = json.dumps(value, ensure_ascii=False)
                    self.js_context.eval(f"var {key} = JSON.parse({json.dumps(js_value)});")
                elif isinstance(value, str):
                    self.js_context.eval(f"var {key} = {json.dumps(value)};")
                elif isinstance(value, (int, float, bool)) or value is None:
                    self.js_context.eval(f"var {key} = {json.dumps(value)};")
                else:
                    js_value = json.dumps(str(value))
                    self.js_context.eval(f"var {key} = {js_value};")
            except Exception as e:
                logger.warning(f"Failed to set JavaScript context variable '{key}': {e}")
    
    def _convert_js_to_python(self, js_result: Any, expression: str) -> Any:
        """Convert JavaScript result back to Python object."""
        try:
            # For simple types, return directly
            if isinstance(js_result, (int, float, bool, type(None))):
                return js_result
            
            # For complex types, use JSON conversion
            json_str = self.js_context.eval(f"JSON.stringify(({expression}))")
            return json.loads(json_str)
        except:
            # Fallback: return the raw result
            return js_result
    
    def _evaluate_fallback(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any]) -> Any:
        """Fallback JavaScript evaluation using Python with basic syntax conversion."""
        try:
            clean_expression = self.extract_expression(expression)
            
            # Basic JS to Python syntax conversion  
            converted = clean_expression
            
            result = eval(converted, {"__builtins__": {}}, context)
            return self.format_result(result, expected_result_type)
            
        except Exception as e:
            raise ExpressionEvaluationError(
                strategy_name="JavaScriptFallback",
                expression=expression,
                step_info=step_info,
                original_error=e
            )


class PythonExpressionStrategy(ExpressionStrategy):
    """Strategy for evaluating Python expressions: [! expression !]"""
    
    def can_handle(self, expression: str) -> bool:
        """Check if expression uses Python syntax: [! ... !]"""
        # Must be exactly a single pure Python expression
        expression = expression.strip()
        if not (expression.startswith('[! ') and expression.endswith(' !]') and len(expression) > 6):
            return False
        
        # Count occurrences to ensure it's a single pure expression
        return expression.count('[!') == 1 and expression.count('!]') == 1
    
    def evaluate(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any] = None) -> Any:
        """Evaluate Python expression."""
        step_info = step_info or {}
        
        try:
            clean_expression = self.extract_expression(expression)
            
            # Create safe evaluation context
            eval_context = {
                **context,
                'json': json,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'sum': sum,
                'max': max,
                'min': min,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'range': range,
            }
            
            # Evaluate Python expression
            result = eval(clean_expression, {"__builtins__": {}}, eval_context)
            
            return self.format_result(result, expected_result_type)
            
        except Exception as e:
            raise ExpressionEvaluationError(
                strategy_name="Python",
                expression=expression,
                step_info=step_info,
                original_error=e
            )


class PlainTextStrategy(ExpressionStrategy):
    """Strategy for handling plain text (no expression syntax)"""
    
    def can_handle(self, expression: str) -> bool:
        """Handle any expression that is NOT a pure single expression"""
        # Pure single expressions: "{! code !}" or "[! code !]" 
        # Everything else (including mixed text with expressions) goes here
        return not self._is_pure_single_expression(expression)
    
    def _is_pure_single_expression(self, text: str) -> bool:
        """Check if text is exactly one pure expression with no extra text."""
        text = text.strip()
        
        # Check if it's exactly a JS expression
        if text.startswith('{! ') and text.endswith(' !}'):
            # Make sure there's no text before or after
            return len(text) > 6 and text.count('{!') == 1 and text.count('!}') == 1
        
        # Check if it's exactly a Python expression  
        if text.startswith('[! ') and text.endswith(' !]'):
            # Make sure there's no text before or after
            return len(text) > 6 and text.count('[!') == 1 and text.count('!]') == 1
            
        return False
    
    def evaluate(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any] = None) -> Any:
        """Process mixed text with expressions or return plain text as-is."""
        # Check if text contains expressions that need processing
        if self._contains_expressions(expression):
            # Use recursive processing for mixed text
            return self._process_mixed_text(expression, context, expected_result_type, step_info)
        else:
            # Pure plain text - return as-is
            return self.format_result(expression, expected_result_type)
    
    def _contains_expressions(self, text: str) -> bool:
        """Check if text contains any expressions."""
        return ('{! ' in text and ' !}' in text) or ('[! ' in text and ' !]' in text)
    
    def _process_mixed_text(self, text: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any]) -> Any:
        """Process mixed text with expressions recursively."""
        # Import here to avoid circular imports
        from . import expressions
        
        # Create a recursive strategy instance for processing
        recursive_strategy = RecursiveExpressionStrategy()
        result_text = recursive_strategy._process_recursive(text, context, step_info or {})
        
        return self.format_result(result_text, expected_result_type)


class RecursiveExpressionStrategy(ExpressionStrategy):
    """Strategy for processing text with nested expressions recursively."""
    
    def __init__(self):
        # Sub-strategies for different expression types
        self.js_strategy = JavaScriptExpressionStrategy()
        self.py_strategy = PythonExpressionStrategy()
        self.plain_strategy = PlainTextStrategy()
    
    def can_handle(self, expression: str) -> bool:
        """Handle text that contains expressions but is not a pure single expression."""
        if not self._contains_expressions(expression):
            return False
            
        # Handle text with expressions (single or multiple)
        return True
    
    def evaluate(self, expression: str, context: Dict[str, Any], expected_result_type: str, step_info: Dict[str, Any] = None) -> Any:
        """Recursively process all expressions in text from innermost to outermost."""
        step_info = step_info or {}
        
        try:
            # If it's a single expression without any other text, delegate to sub-strategies
            if self._is_single_expression(expression):
                for strategy in [self.js_strategy, self.py_strategy]:
                    if strategy.can_handle(expression):
                        return strategy.evaluate(expression, context, expected_result_type, step_info)
            
            # Otherwise process recursively for mixed text with expressions
            result_text = self._process_recursive(expression, context, step_info)
            
            # After recursive processing, check if the result became a single expression
            if self._is_single_expression(result_text):
                for strategy in [self.js_strategy, self.py_strategy]:
                    if strategy.can_handle(result_text):
                        return strategy.evaluate(result_text, context, expected_result_type, step_info)
            
            # Otherwise return as plain text (mixed text should not be JSON-encoded)
            return result_text
            
        except Exception as e:
            raise ExpressionEvaluationError(
                strategy_name="Recursive",
                expression=expression,
                step_info=step_info,
                original_error=e
            )
    
    def _process_recursive(self, text: str, context: Dict[str, Any], step_info: Dict[str, Any]) -> str:
        """Process expressions recursively from innermost to outermost."""
        max_iterations = 100  # защита от бесконечных циклов
        iteration = 0
        
        while self._contains_expressions(text) and iteration < max_iterations:
            # Find ALL expressions (not just innermost)
            expressions = self._find_all_expressions(text)
            
            if not expressions:
                break
            
            # Process each expression (from right to left to preserve positions)
            processed_any = False
            for expr_info in reversed(expressions):
                expr_text = expr_info['text']
                start_pos = expr_info['start']
                end_pos = expr_info['end']
                
                # Skip if this expression contains other expressions (process inner first)
                expr_content = expr_text[3:-3]  # Remove {! !} or [! !]
                if self._contains_expressions(expr_content):
                    continue
                
                # Evaluate the expression
                result = self._evaluate_single_expression(expr_text, context, step_info)
                
                # Replace in text
                text = text[:start_pos] + str(result) + text[end_pos:]
                processed_any = True
            
            # If no expressions were processed, break to avoid infinite loop
            if not processed_any:
                break
                
            iteration += 1
        
        if iteration >= max_iterations:
            logger.warning(f"Recursive expression processing hit max iterations for: {text[:100]}...")
        
        return text
    
    def _find_all_expressions(self, text: str) -> List[Dict[str, Any]]:
        """Find all expressions with proper nesting handling."""
        expressions = []
        
        # Find all expressions with proper nesting handling
        js_expressions = self._find_expressions_with_nesting(text, '{!', '!}')
        py_expressions = self._find_expressions_with_nesting(text, '[!', '!]')
        
        all_expressions = js_expressions + py_expressions
        
        # Sort by position to process from left to right
        return sorted(all_expressions, key=lambda x: x['start'])
    
    def _find_expressions_with_nesting(self, text: str, start_marker: str, end_marker: str) -> List[Dict[str, Any]]:
        """Find expressions with proper nesting handling."""
        expressions = []
        i = 0
        
        while i < len(text):
            start_pos = text.find(start_marker, i)
            if start_pos == -1:
                break
            
            # Check for required space after start marker
            if start_pos + len(start_marker) >= len(text) or text[start_pos + len(start_marker)] != ' ':
                i = start_pos + 1
                continue
            
            # Find matching end marker with nesting support
            end_pos = self._find_matching_end(text, start_pos, start_marker, end_marker)
            if end_pos == -1:
                i = start_pos + 1
                continue
            
            # Check for required space before end marker
            if end_pos == 0 or text[end_pos - 1] != ' ':
                i = start_pos + 1
                continue
            
            expr_text = text[start_pos:end_pos + len(end_marker)]
            expressions.append({
                'text': expr_text,
                'start': start_pos,
                'end': end_pos + len(end_marker)
            })
            
            i = end_pos + 1
        
        return expressions
    
    def _find_matching_end(self, text: str, start_pos: int, start_marker: str, end_marker: str) -> int:
        """Find matching end marker with proper nesting handling."""
        nesting_level = 0
        i = start_pos + len(start_marker)
        in_string = False
        string_char = None
        escape_next = False
        
        while i < len(text):
            if escape_next:
                escape_next = False
                i += 1
                continue
            
            char = text[i]
            
            if char == '\\':
                escape_next = True
                i += 1
                continue
            
            if not in_string:
                if char in ['"', "'", '`']:
                    in_string = True
                    string_char = char
                elif text[i:].startswith(start_marker):
                    nesting_level += 1
                    i += len(start_marker) - 1
                elif text[i:].startswith(end_marker):
                    if nesting_level == 0:
                        return i
                    nesting_level -= 1
                    i += len(end_marker) - 1
            else:
                if char == string_char:
                    in_string = False
                    string_char = None
            
            i += 1
        
        return -1
    
    def _evaluate_single_expression(self, expr_text: str, context: Dict[str, Any], step_info: Dict[str, Any]) -> Any:
        """Evaluate a single expression using appropriate strategy."""
        for strategy in [self.js_strategy, self.py_strategy]:
            if strategy.can_handle(expr_text):
                return strategy.evaluate(expr_text, context, "python", step_info)
        
        # Fallback to plain text
        return expr_text
    
    def _contains_expressions(self, text: str) -> bool:
        """Check if text contains any expressions."""
        return ('{! ' in text and ' !}' in text) or ('[! ' in text and ' !]' in text)
    
    def _is_single_expression(self, text: str) -> bool:
        """Check if text is a single expression."""
        text = text.strip()
        return ((text.startswith('{! ') and text.endswith(' !}')) or 
                (text.startswith('[! ') and text.endswith(' !]')))


# Global registry of expression strategies
_strategies: List[ExpressionStrategy] = [
    JavaScriptExpressionStrategy(), # First - handles pure JS expressions: {! expr !}
    PythonExpressionStrategy(),     # Second - handles pure Python expressions: [! expr !]
    RecursiveExpressionStrategy(),  # Third - handles mixed text with expressions
    PlainTextStrategy()             # Last - fallback for plain text
]


def evaluate_expression(expression: str, context: Dict[str, Any], expected_result_type: str = "python", step_info: Dict[str, Any] = None) -> Any:
    """
    Universal expression evaluation function.
    
    Args:
        expression: Expression to evaluate ("{! js_expr !}", "[! py_expr !]", or plain text)
        context: Dictionary of native Python objects 
        expected_result_type: "python" (returns Python objects) or "json" (returns JSON strings)
        step_info: Pipeline step information for error reporting
        
    Returns:
        Evaluated result in specified format
        
    Raises:
        ExpressionEvaluationError: If evaluation fails
    """
    logger.debug(f"evaluate_expression: {expression!r}, expected_type: {expected_result_type}")
    
    # Build context with built-in variables (env, etc.) + user context
    full_context = build_default_context(context)
    
    # Try each strategy
    for strategy in _strategies:
        if strategy.can_handle(expression):
            logger.debug(f"Using strategy: {strategy.__class__.__name__}")
            result = strategy.evaluate(expression, full_context, expected_result_type, step_info)
            # logger.debug(f"Strategy result: {result!r}, type: {type(result)}")
            return result
    
    logger.debug("No strategy could handle expression, using fallback")
    # Fallback for plain text
    if expected_result_type == "python":
        return None
    elif expected_result_type == "json":
        return "null"
    else:
        raise ValueError(f"Unknown expected_result_type: {expected_result_type}")


def contains_expressions(text: str) -> bool:
    """Check if text contains any evaluable expressions."""
    return bool(re.search(r'\{! .+ !\}|\[! .+ !\]', text))


def substitute_expressions(text: str, context: Dict[str, Any], expected_result_type: str = "json", step_info: Dict[str, Any] = None) -> str:
    """
    Replace all expressions in text with their evaluated values.
    
    Args:
        text: Text containing expressions
        context: Dictionary of native Python objects
        expected_result_type: "python" or "json"  
        step_info: Pipeline step information for error reporting
        
    Returns:
        Text with all expressions replaced by their evaluated values
    """
    if not contains_expressions(text):
        return text
    
    # Use the global evaluation function that handles strategy selection properly
    result = evaluate_expression(text, context, expected_result_type, step_info)
    
    if expected_result_type == "json" and not isinstance(result, str):
        return json.dumps(result, ensure_ascii=False)

    return str(result)
def substitute_in_object(obj: Any, context: Dict[str, Any], step_info: Dict[str, Any] = None, preserve_objects: bool = False) -> Any:
    """
    Универсальная функция для подстановки выражений в объектах.
    
    Любая строка проходит через единую точку обработки выражений.
    
    Args:
        obj: Объект для обработки (dict, list, str, или примитив)
        context: Контекст с переменными
        step_info: Информация о шаге для отладки
        preserve_objects: Если True, одиночные выражения возвращают Python объекты,
                         если False - все результаты приводятся к строкам
        
    Returns:
        Объект с подставленными выражениями
    """
    if isinstance(obj, dict):
        return {k: substitute_in_object(v, context, step_info, preserve_objects) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_in_object(item, context, step_info, preserve_objects) for item in obj]
    elif isinstance(obj, str):
        # Проверяем наличие выражений (старый и новый синтаксис)
        if "{!" in obj or "[!" in obj:
            obj_stripped = obj.strip()
            
            # Проверяем, является ли это одиночным выражением
            is_single_expression = (
                (obj_stripped.startswith('{! ') and obj_stripped.endswith(' !}')) or 
                (obj_stripped.startswith('[! ') and obj_stripped.endswith(' !]'))
            )
            
            if preserve_objects and is_single_expression:
                # Для одиночных выражений с preserve_objects=True возвращаем Python объекты
                return evaluate_expression(obj_stripped, context, expected_result_type="python", step_info=step_info)
            elif is_single_expression:
                # Для одиночных выражений с preserve_objects=False возвращаем значения без JSON кавычек
                result = evaluate_expression(obj_stripped, context, expected_result_type="python", step_info=step_info)
                # Если результат - строка, возвращаем как есть. Если объект - конвертируем в JSON строку
                if isinstance(result, str):
                    return result
                else:
                    return json.dumps(result, ensure_ascii=False)
            else:
                # Для смешанного текста - возвращаем строки с правильной подстановкой
                return substitute_expressions(obj, context, expected_result_type="json", step_info=step_info)
        return obj
    else:
        return obj


def parse_substituted_string(text: str, context: Dict[str, Any] = None) -> Any:
    """
    Парсит строку после подстановки выражений в нативный Python объект.
    
    Это функция для стратегий, которые хотят интерпретировать строку
    как Python объект (например, forEach нужен list, а не строка "[1,2,3]").
    
    Args:
        text: Строка после подстановки выражений
        context: Контекст (для отладки)
        
    Returns:
        Python объект или исходная строка, если парсинг не удался
    """
    if not isinstance(text, str):
        return text
        
    text = text.strip()
    
    # Попробуем распарсить как JSON
    try:
        import json
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Если не JSON, возвращаем как строку
    return text
