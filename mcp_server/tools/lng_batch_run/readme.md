# lng_batch_run

Executes a batch pipeline of tool calls with variable substitution using JavaScript expressions.

**⚡ Now powered by modular strategy architecture for maximum extensibility!**

## Features

- **Sequential execution** - Tools run one after another
- **Variable passing** - Store results and use in subsequent steps
- **JavaScript expressions** - Use `{! expression !}` syntax for data manipulation
- **Python expressions** - Use `[! expression !]` syntax for Python-based calculations
- **Conditional logic** - `if/then/else` statements with expression evaluation
- **Loop support** - `forEach`, `while`, and `repeat` iterations
- **Parallel execution** - Run multiple tools simultaneously
- **Timing control** - Delays and precise timing operations
- **JSON parsing** - Automatic parsing of tool responses
- **Property access** - Access object properties with `obj.property` syntax
- **Error handling** - Detailed error reporting with execution context
- **Modular architecture** - Built on strategy pattern for easy extension

## Usage

```bash
python -m mcp_server.run run lng_batch_run '{
  "pipeline": [
    {
      "tool": "tool_name",
      "params": {"param": "{! variable !}"},
      "output": "variable_name"
    }
  ],
  "final_result": "{! result_expression !}"
}'
```

### Three-step pipeline example

```bash
python -m mcp_server.run run lng_batch_run '{
  "pipeline": [
    {
      "tool": "lng_winapi_clipboard_get",
      "params": {},
      "output": "clipboard_content"
    },
    {
      "tool": "lng_count_words",
      "params": {"input_text": "{! clipboard_content.content !}"},
      "output": "word_stats"
    },
    {
      "tool": "lng_winapi_clipboard_set",
      "params": {"text": "Analysis: {! word_stats.wordCount !} words, {! word_stats.charactersWithSpaces !} chars"}
    }
  ],
  "final_result": "Text analysis completed with {! word_stats.wordCount !} words"
}'
```

## Pipeline Structure

- **pipeline** - Array of steps to execute
- **tool** - Name of the MCP tool to call
- **params** - Parameters to pass (supports variable substitution)
- **output** - Variable name to store the result (optional)
- **final_result** - Expression for the final return value (optional, default: "ok")

## Variable Substitution

Variables are substituted using expression syntax:

**JavaScript expressions:**
- `{! variable !}` - Direct variable access
- `{! variable.property !}` - Object property access
- `{! variable || 'default' !}` - Fallback values
- `{! variable ? 'yes' : 'no' !}` - Conditional expressions
- `{! JSON.stringify(variable) !}` - JSON serialization

**Python expressions:**
- `[! variable !]` - Direct variable access
- `[! len(variable) if variable else 0 !]` - Python conditional expressions
- `[! sum(item.value for item in variable) !]` - Python comprehensions

## Examples

### Simple clipboard operations
```json
{
  "pipeline": [
    {"tool": "lng_winapi_clipboard_get", "params": {}, "output": "clipboard_text"},
    {"tool": "lng_winapi_clipboard_set", "params": {"text": "{! clipboard_text.content !}"}}
  ],
  "final_result": "ok"
}
```

### Text processing chain
```json
{
  "pipeline": [
    {"tool": "lng_winapi_clipboard_get", "params": {}, "output": "text"},
    {"tool": "lng_count_words", "params": {"input_text": "{! text.content !}"}, "output": "count"},
    {"tool": "lng_winapi_clipboard_set", "params": {"text": "Words: {! count.wordCount !}"}}
  ],
  "final_result": "completed"
}
```

## New Response Format

The pipeline now returns a structured response with more details:

```json
{
  "success": true,
  "result": "final_result_value",
  "error": null,
  "step": null,
  "tool": null,
  "context": {
    "variable1": "value1",
    "variable2": "value2"
  },
  "execution_time": 0.002
}
```

## Error Handling

If any step fails, execution stops and returns:
```json
{
  "success": false,
  "error": "Step 2 failed: error description",
  "step": 2,
  "tool": "tool_name",
  "context": {"var1": "value1", "var2": "value2"},
  "execution_time": 0.001
}
```

### Advanced Pipeline Features ✨

**NEW**: Support for complex pipeline logic with modular strategy architecture!

#### Conditional Logic
```json
{
  "type": "condition",
  "condition": "{! stats.wordCount > 10 !}",
  "then": [
    {"tool": "lng_winapi_clipboard_set", "params": {"text": "Long text: {! stats.wordCount !} words"}}
  ],
  "else": [
    {"tool": "lng_winapi_clipboard_set", "params": {"text": "Short text: {! stats.wordCount !} words"}}
  ]
}
```

#### Loop Operations
```json
{
  "type": "forEach",
  "forEach": "{! collection !}",
  "item": "current_item",
  "do": [
    {"tool": "lng_count_words", "params": {"input_text": "{! current_item !}"}, "output": "stats_{! current_item !}"}
  ]
}
```

#### Parallel Execution
```json
{
  "type": "parallel",
  "parallel": [
    {"tool": "lng_count_words", "params": {"input_text": "Text 1"}, "output": "stats1"},
    {"tool": "lng_math_calculator", "params": {"expression": "2 + 2"}, "output": "calc1"}
  ]
}
```

#### Timing Control
```json
{
  "type": "delay",
  "delay": 1.5
}
```

## Architecture

Built on modular strategy pattern with 5 core strategies:
- **Tool Strategy**: Basic tool execution with parameter substitution
- **Conditional Strategy**: If-then-else logic with JavaScript expressions
- **Loop Strategy**: forEach, while, and repeat iterations
- **Parallel Strategy**: Concurrent execution of multiple steps
- **Delay Strategy**: Timing operations and delays

Each strategy is independently tested and easily extensible.

## Integration

Designed for use with hotkey listener for automated workflows:
1. Register hotkey → batch tool
2. Define pipeline in tool parameters
3. Execute complex operations with single keypress

## File-Based Pipeline Configuration 📁

**NEW**: Support for external pipeline configuration files for better organization and reusability!

### Parameters

- **pipeline_file** (string, optional) - Path to JSON file containing pipeline configuration
- **pipeline** (array, optional) - Direct pipeline definition (if pipeline_file not provided)

**Note**: Either `pipeline_file` or `pipeline` parameter is required.

### Usage with Configuration Files

```bash
python -m mcp_server.run run lng_batch_run '{
  "pipeline_file": "path/to/pipeline_config.json"
}'
```

### File-based Pipeline Example

Create a JSON file with your pipeline configuration:

**telemetry_pipeline.json**:
```json
{
  "pipeline": [
    {
      "tool": "lng_file_read",
      "params": {"file_path": "data/telemetry.json"},
      "output": "telemetry_data"
    },
    {
      "tool": "lng_json_to_csv",
      "params": {"json_data": "{! JSON.parse(telemetry_data) !}"},
      "output": "csv_result"
    },
    {
      "tool": "lng_file_write",
      "params": {
        "file_path": "output/telemetry_report.csv",
        "content": "{! csv_result !}"
      }
    }
  ],
  "final_result": "Telemetry report generated successfully"
}
```

### Benefits of File-Based Configuration

- **Reusability**: Share pipelines across different executions
- **Version Control**: Track pipeline changes in git
- **Organization**: Keep complex pipelines in separate files
- **Maintenance**: Easier to edit and debug large pipelines
- **Parameter Override**: Can still override `final_result` and other parameters

### Parameter Merging

When using `pipeline_file`, you can still override specific parameters:

```bash
python -m mcp_server.run run lng_batch_run '{
  "pipeline_file": "config/basic_pipeline.json",
  "final_result": "Custom result: {! stats.wordCount !} words processed"
}'
```
