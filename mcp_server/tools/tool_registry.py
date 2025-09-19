import os
import logging
import traceback
import yaml
from importlib import import_module
from pathlib import Path
from mcp_server.logging_config import setup_logging

logger = setup_logging('mcp_server', logging.DEBUG)

tool_definitions = []

def is_tool_disabled(tool_path: Path) -> tuple[bool, str]:
    """Check if tool or tool group is disabled via settings.yaml"""
    current_path = tool_path
    
    # Check current directory and all parent directories up to tools/
    while current_path.name != 'tools' and current_path != current_path.parent:
        settings_file = current_path / 'settings.yaml'
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = yaml.safe_load(f)
                    if settings and not settings.get('enabled', True):
                        description = settings.get('description', 'Tool is disabled via settings.yaml')
                        return True, description
            except Exception as e:
                logger.warning(f"Error reading settings file {settings_file}: {e}")
        current_path = current_path.parent
    
    return False, ""

def handle_problem_imports():
    """Handle problematic imports for all enabled tools that have a problem_imports method."""
    logger.info("Starting to handle problem imports for enabled tools")
    
    # Get the directory where this file is located
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"Scanning tools directory for problem imports: {current_dir}")
    
    def scan_directory_for_imports(directory: Path, prefix_parts: list = []):
        """Recursively scan directory for tools with problem_imports method."""
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                current_prefix_parts = prefix_parts + [item.name]
                
                # Check if there's a tool.py file in the current directory
                tool_file = item / 'tool.py'
                if tool_file.exists():
                    # Check if tool is disabled
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping problem imports for disabled tool: {item.name} - {description}")
                        continue
                    
                    # Build module path and try to import
                    module_path = f"mcp_server.tools.{'.'.join(current_prefix_parts)}.tool"
                    tool_name = '_'.join(current_prefix_parts)
                    
                    try:
                        logger.info(f"Checking tool {tool_name} for problem_imports method")
                        module = import_module(module_path)
                        
                        # Check if the module has a problem_imports function
                        if hasattr(module, 'problem_imports'):
                            logger.info(f"Found problem_imports method in {tool_name}, calling it")
                            try:
                                module.problem_imports()
                                logger.info(f"Successfully executed problem_imports for {tool_name}")
                            except Exception as e:
                                logger.error(f"Error executing problem_imports for {tool_name}: {e}")
                                logger.error(traceback.format_exc())
                        else:
                            logger.debug(f"No problem_imports method found in {tool_name}")
                            
                    except Exception as e:
                        logger.error(f"Error importing module {module_path} for problem imports: {e}")
                        logger.error(traceback.format_exc())
                else:
                    # If no tool.py in current directory, continue scanning subdirectories
                    # Check if the directory itself is disabled before scanning subdirectories
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping problem imports for disabled tool group: {item.name} - {description}")
                        continue
                    # Always recurse into subdirectories to find tools at any depth
                    scan_directory_for_imports(item, current_prefix_parts)
    
    # Start scanning from the tools directory
    scan_directory_for_imports(current_dir)
    logger.info("Completed handling problem imports for all enabled tools")

def initialize_tools():
    """Initialize all enabled tools that have an init method."""
    logger.info("Starting to initialize enabled tools")
    
    # Get the directory where this file is located
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"Scanning tools directory for initialization: {current_dir}")
    
    def scan_directory_for_init(directory: Path, prefix_parts: list = []):
        """Recursively scan directory for tools with init method."""
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                current_prefix_parts = prefix_parts + [item.name]
                
                # Check if there's a tool.py file in the current directory
                tool_file = item / 'tool.py'
                if tool_file.exists():
                    # Check if tool is disabled
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping initialization for disabled tool: {item.name} - {description}")
                        continue
                    
                    # Build module path and try to import
                    module_path = f"mcp_server.tools.{'.'.join(current_prefix_parts)}.tool"
                    tool_name = '_'.join(current_prefix_parts)
                    
                    try:
                        logger.info(f"Checking tool {tool_name} for init method")
                        module = import_module(module_path)
                        
                        # Check if the module has an init function
                        if hasattr(module, 'init'):
                            logger.info(f"Found init method in {tool_name}, calling it")
                            try:
                                module.init()
                                logger.info(f"Successfully executed init for {tool_name}")
                            except Exception as e:
                                logger.error(f"Error executing init for {tool_name}: {e}")
                                logger.error(traceback.format_exc())
                        else:
                            logger.debug(f"No init method found in {tool_name}")
                            
                    except Exception as e:
                        logger.error(f"Error importing module {module_path} for initialization: {e}")
                        logger.error(traceback.format_exc())
                else:
                    # If no tool.py in current directory, continue scanning subdirectories
                    # Check if the directory itself is disabled before scanning subdirectories
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping initialization for disabled tool group: {item.name} - {description}")
                        continue
                    # Always recurse into subdirectories to find tools at any depth
                    scan_directory_for_init(item, current_prefix_parts)
    
    # Start scanning from the tools directory
    scan_directory_for_init(current_dir)
    logger.info("Completed initializing all enabled tools")

def register_tool(name: str, module_path: str):
    """Registers a tool with its name and module path."""
    tool_definitions.append({"name": name, "module_path": module_path})

async def get_tool_info(name: str):
    """Retrieves the tool information based on the tool name."""
    try:
        for tool in tool_definitions:
            if tool["name"] == name:
                logger.info(f"Getting info for tool: {name}, module path: {tool['module_path']}")
                try:
                    module = import_module(tool["module_path"])
                    logger.info(f"Successfully imported module for tool: {name}")
                    tool_info = await module.tool_info()
                    tool_info["name"] = name
                    logger.info(f"Successfully retrieved info for tool: {name}")
                    return tool_info
                except Exception as e:
                    logger.error(f"Error getting info for tool {name}: {e}")
                    logger.error(traceback.format_exc())
                    # Return a minimal tool info to prevent breaking the entire list
                    return {
                        "name": name,
                        "description": f"Error loading tool: {str(e)}",
                        "schema": {"type": "object", "properties": {}}
                    }
        logger.warning(f"Tool '{name}' not found.")
        raise ValueError(f"Tool '{name}' not found.")
    except Exception as e:
        logger.error(f"Unexpected error in get_tool_info for {name}: {e}")
        logger.error(traceback.format_exc())
        # Return a minimal tool info to prevent breaking the entire list
        return {
            "name": name,
            "description": f"Error loading tool: {str(e)}",
            "schema": {"type": "object", "properties": {}}
        }

async def tools_info():
    """Returns information about all registered tools."""
    logger.info(f"Retrieving info for {len(tool_definitions)} registered tools")
    results = []
    for tool in tool_definitions:
        try:
            logger.info(f"Getting info for tool: {tool['name']}")
            info = await get_tool_info(tool["name"])
            results.append(info)
            logger.info(f"Successfully added info for tool: {tool['name']}")
        except Exception as e:
            logger.error(f"Error processing tool {tool['name']}: {e}")
            logger.error(traceback.format_exc())
            # Add minimal info to not break the entire list
            results.append({
                "name": tool["name"],
                "description": f"Error loading tool: {str(e)}",
                "schema": {"type": "object", "properties": {}}
            })
    logger.info(f"Returning info for {len(results)} tools")
    return results

def register_tools():
    """Registers all tools in the project by automatically scanning the tools directory."""
    logger.info("Starting to register tools")
    
    # Get the directory where this file is located
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"Scanning tools directory: {current_dir}")
    
    tool_count = 0
    
    def scan_directory(directory: Path, prefix_parts: list = []):
        """Recursively scan directory for tools."""
        nonlocal tool_count
        
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                current_prefix_parts = prefix_parts + [item.name]
                
                # Check if there's a tool.py file in the current directory
                tool_file = item / 'tool.py'
                if tool_file.exists():
                    # Check if tool is disabled
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping disabled tool: {item.name} - {description}")
                        continue
                    
                    # Build tool name from all path parts
                    tool_name = '_'.join(current_prefix_parts)
                    # Build module path
                    module_path = f"mcp_server.tools.{'.'.join(current_prefix_parts)}.tool"
                    
                    register_tool(tool_name, module_path)
                    logger.info(f"Registered tool: {tool_name} (module: {module_path})")
                    tool_count += 1
                else:
                    # If no tool.py in current directory, continue scanning subdirectories
                    # Check if the directory itself is disabled before scanning subdirectories
                    is_disabled, description = is_tool_disabled(item)
                    if is_disabled:
                        logger.info(f"Skipping disabled tool group: {item.name} - {description}")
                        continue
                    # Always recurse into subdirectories to find tools at any depth
                    scan_directory(item, current_prefix_parts)
    
    # Start scanning from the tools directory
    scan_directory(current_dir)
    
    logger.info(f"Registered a total of {tool_count} tools")
    
async def run_tool(name: str, arguments: dict) -> list:
    """Runs the specified tool with the provided arguments."""
    logger.info(f"Running tool: {name} with arguments: {arguments}")
    
    try:
        for tool in tool_definitions:
            if tool["name"] == name:
                logger.info(f"Found tool {name}, importing module {tool['module_path']}")
                try:
                    module = import_module(tool["module_path"])
                    logger.info(f"Successfully imported module for tool: {name}")
                    result = await module.run_tool(name, arguments)
                    logger.info(f"Tool {name} executed successfully")
                    return result
                except Exception as e:
                    logger.error(f"Error running tool {name}: {e}")
                    logger.error(traceback.format_exc())
                    raise
        
        logger.warning(f"Tool '{name}' not found.")
        raise ValueError(f"Tool '{name}' not found.")
    except Exception as e:
        logger.error(f"Unexpected error in run_tool for {name}: {e}")
        logger.error(traceback.format_exc())
        raise

register_tools()

# Initialize all tools after registration
logger.info("Starting tool initialization after registration")
initialize_tools()
logger.info("Tool initialization completed")