# Development and Testing Files

This folder contains development files that were used during the creation of the multi-agent system.

## Files

### Test Files
- `test_basic.py` - Basic functionality tests without LLM calls
- `test_system.py` - Full system tests with LLM integration (requires Azure OpenAI)

### Documentation
- `architecture.md` - Detailed architecture documentation and design decisions
- `demo.md` - Demo scenarios and usage examples

## Usage

These tests can be used to verify the multi-agent system functionality during development or debugging.

### Running Tests

```bash
# Basic tests (no LLM required)
python mcp_server/tools/lng_multi_agent/stuff/test_basic.py

# Full system tests (requires LLM)
python mcp_server/tools/lng_multi_agent/stuff/test_system.py
```

## Note

These files are kept for reference and debugging purposes but are not part of the production system.
