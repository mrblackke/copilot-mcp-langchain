# Library Analysis Tools

This module contains tools for analyzing Python libraries for security and licensing compliance criteria.

## Usage

### Via main run script (recommended):

```bash
# Analyze a single library
python -m mcp_server.run analyze_libs langchain

# Analyze multiple libraries
python -m mcp_server.run analyze_libs langchain requests numpy

# Analyze all libraries from the project
python -m mcp_server.run analyze_libs langchain langchain-openai langchain-community langchain-experimental langchain-text-splitters faiss-cpu mss aiohttp pywinauto psutil pywin32
```

### Direct module usage:

```bash
python -m mcp_server.libs.analyzer langchain requests
```

## What is analyzed

For each library, the following is checked:

- ✅ **License** - open source license (MIT, Apache, BSD, GPL, etc.)
- ✅ **Recency** - last update date
- ✅ **Compatibility** - Python version requirements
- ✅ **Documentation** - presence of homepage and documentation
- ✅ **Support** - author/maintainer information

## Scoring System

- **RECOMMENDED** (70+ points) - ✅ Recommended for use
- **CONDITIONALLY_RECOMMENDED** (50-69 points) - ⚠️ Can be used with caution
- **NEEDS_REVIEW** (30-49 points) - 🔍 Requires additional review
- **NOT_RECOMMENDED** (<30 points) - ❌ Not recommended for use
- **ERROR** - 💥 Error retrieving information

## Project Instruction Compliance Criteria

According to `mcp_server/instructions/choose-library.agent.md`:

1. Choose the most open source libraries
2. Use PyPI to get library information
3. Do not use libraries without open source licenses
4. Do not use libraries that haven't been updated for a long time or contain vulnerabilities

The analyzer automatically checks these criteria and provides recommendations.
