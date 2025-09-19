"""
Common logging configuration for MCP server components.
Provides unified logging setup for both server.py and run.py.
"""
import os
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(component_name: str, log_level: int = logging.DEBUG) -> logging.Logger:
    """
    Setup logging configuration for MCP server components.
    
    Args:
        component_name: Name of the component (used for logger name and log file)
        log_level: Logging level (default: DEBUG)
    
    Returns:
        Configured logger instance
    """
    # Determine log file path based on component name
    current_dir = Path(__file__).parent
    log_dir = current_dir / "logs"
    log_file = log_dir / f"{component_name}.log"
    
    # Ensure logs directory exists
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(component_name)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set logging level
    logger.setLevel(log_level)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Create detailed formatter with maximum information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add file handler (always)
    logger.addHandler(file_handler)
    
    # Detect if we're running in MCP server mode
    is_mcp_server = (
        "mcp" in sys.argv[0].lower() or 
        any("mcp" in arg for arg in sys.argv) or
        os.getenv("MCP_MODE") == "true"
    )
    
    # Detect if we're running as a standalone tool runner (run.py)
    is_tool_runner = (
        "run.py" in sys.argv[0] or 
        "mcp_server.run" in sys.argv[0] or
        (len(sys.argv) > 1 and sys.argv[1] in ['list', 'run', 'batch', 'schema', 'install_dependencies', 'analyze_libs'])
    )
    
    # Add console handler for standalone tool runner (but not for MCP server)
    if not is_mcp_server and is_tool_runner:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging initialized for {component_name}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def setup_instance_logger(instance_name: str, log_subdir: str, logger_prefix: str = None) -> logging.Logger:
    """
    Setup dedicated logger for specific instances (webhooks, websockets, etc.).
    
    Args:
        instance_name: Name of the instance (e.g., 'cookie-status-custom')
        log_subdir: Subdirectory under logs/ (e.g., 'webhook', 'websocket')
        logger_prefix: Optional prefix for logger name (default: log_subdir)
    
    Returns:
        Configured logger instance
    
    Example:
        logger = setup_instance_logger('my-webhook', 'webhook')
        # Creates: mcp_server/logs/webhook/my-webhook_2025-08-25T21-14-15.log
        # Logger name: webhook.my-webhook
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    
    # Determine log file path
    current_dir = Path(__file__).parent
    log_dir = current_dir / "logs" / log_subdir
    log_file = log_dir / f"{instance_name}_{timestamp}.log"
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create instance-specific logger
    logger_name = f"{logger_prefix or log_subdir}.{instance_name}"
    instance_logger = logging.getLogger(logger_name)
    instance_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in instance_logger.handlers[:]:
        instance_logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Formatter for human-readable logs
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    instance_logger.addHandler(file_handler)
    
    # Prevent propagation to avoid double logging
    instance_logger.propagate = False
    
    return instance_logger


def close_instance_logger(instance_name: str, log_subdir: str, logger_prefix: str = None):
    """
    Properly close and cleanup instance logger to release file handles.
    
    Args:
        instance_name: Name of the instance
        log_subdir: Subdirectory under logs/
        logger_prefix: Optional prefix for logger name
    """
    logger_name = f"{logger_prefix or log_subdir}.{instance_name}"
    instance_logger = logging.getLogger(logger_name)
    
    # Close and remove all handlers
    for handler in instance_logger.handlers[:]:
        if hasattr(handler, 'close'):
            handler.close()
        instance_logger.removeHandler(handler)
    
    # Clear the logger
    instance_logger.handlers.clear()
    instance_logger.filters.clear()