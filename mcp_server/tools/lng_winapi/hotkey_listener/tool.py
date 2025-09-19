import mcp.types as types
import json
import asyncio
import os
import subprocess
import sys
import time
import logging
from pathlib import Path
from mcp_server.logging_config import setup_logging

logger = setup_logging("mcp_server", logging.DEBUG)

# Флаг для отслеживания инициализации
_service_initialized = False

async def run_tool_fast_mode(operation: str, hotkey: str, tool_name: str, tool_json: dict) -> list[types.Content]:
    """Быстрый режим - прямая работа с Windows API без daemon"""
    global _service_initialized
    
    # Автоматическое восстановление хоткеев при первом обращении
    if not _service_initialized:
        logger.debug("First access to hotkey service - attempting to restore saved hotkeys")
        try:
            restore_result = await restore_hotkeys_state()
            if restore_result.get("success"):
                restored_count = restore_result.get("restored_count", 0)
                if restored_count > 0:
                    logger.warning(f"Successfully restored {restored_count} hotkeys from saved state")
                else:
                    logger.debug("No hotkeys to restore")
            else:
                logger.warning(f"Failed to restore hotkeys: {restore_result.get('error')}")
        except Exception as e:
            logger.error(f"Error during hotkeys restoration: {e}")
        finally:
            _service_initialized = True
    
    try:
        if operation == "list":
            # Прямое обращение к hotkey_core
            from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import list_hotkeys
            result = await list_hotkeys()
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif operation == "service_status":
            # Проверяем наличие активных хоткеев через Windows API
            from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import list_hotkeys
            result = await list_hotkeys()
            
            if result.get("success"):
                hotkeys_count = len(result.get("active_hotkeys", []))
                status_result = {
                    "success": True,
                    "running": True,
                    "mode": "fast_api",
                    "hotkeys_count": hotkeys_count,
                    "hotkeys": {hk["hotkey"]: hk for hk in result.get("active_hotkeys", [])},
                    "timestamp": time.time()
                }
            else:
                status_result = {
                    "success": True,
                    "running": False,
                    "mode": "fast_api",
                    "hotkeys_count": 0,
                    "error": result.get("error")
                }
            
            return [types.TextContent(type="text", text=json.dumps(status_result, ensure_ascii=False, indent=2))]
        
        elif operation == "register":
            # Прямая регистрация через Windows API
            from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import register_hotkey
            result = await register_hotkey(hotkey, tool_name, tool_json)
            
            # Сохраняем состояние в файл для постоянства
            if result.get("success"):
                await save_hotkeys_state()
            
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif operation == "unregister":
            # Прямое удаление через Windows API
            from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import unregister_hotkey
            result = await unregister_hotkey(hotkey)
            
            # Сохраняем состояние в файл
            if result.get("success"):
                await save_hotkeys_state()
            
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif operation == "unregister_all":
            # Прямое удаление всех хоткеев через Windows API
            from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import unregister_all_hotkeys
            result = await unregister_all_hotkeys()
            
            # Сохраняем пустое состояние в файл
            if result.get("success"):
                await save_hotkeys_state()
            
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif operation == "restore":
            # Ручное восстановление хоткеев из сохраненного файла
            result = await restore_hotkeys_state()
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif operation in ["start_service", "stop_service"]:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False,
                "error": f"Operation '{operation}' is deprecated. The hotkey system now works directly without a daemon service.",
                "info": "Use 'service_status' to check current state, 'register' to add hotkeys, 'list' to see active hotkeys."
            }, ensure_ascii=False, indent=2))]
        
        else:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False,
                "error": f"Unknown operation: {operation}. Supported operations: service_status, register, unregister, list, unregister_all, restore"
            }, ensure_ascii=False, indent=2))]
            
    except Exception as e:
        logger.error(f"Error in fast mode: {e}")
        return [types.TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"Fast mode error: {str(e)}"
        }, ensure_ascii=False, indent=2))]

async def save_hotkeys_state():
    """Простое сохранение состояния хоткеев для постоянства"""
    try:
        from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import list_hotkeys
        result = await list_hotkeys()
        
        if result.get("success"):
            # Сохраняем в том же формате, что и daemon
            status_file = Path(__file__).parent.parent.parent.parent / "config/hotkey" / "hotkey_service_status.json"
            status_file.parent.mkdir(exist_ok=True)
            
            status = {
                "mode": "fast_api",
                "hotkeys": {hk["hotkey"]: {
                    "tool_name": hk["tool_name"],
                    "tool_json": hk["tool_json"],
                    "hotkey_id": hk["hotkey_id"]
                } for hk in result.get("active_hotkeys", [])},
                "running": True,
                "timestamp": time.time()
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
                
    except Exception as e:
        logger.error(f"Error saving hotkeys state: {e}")

async def restore_hotkeys_state():
    """Восстановление хоткеев из сохраненного состояния при запуске"""
    try:
        status_file = Path(__file__).parent.parent.parent.parent / "config/hotkey" / "hotkey_service_status.json"
        
        if not status_file.exists():
            logger.info("No saved hotkeys state found")
            return {"success": True, "restored_count": 0, "message": "No saved state file"}
        
        with open(status_file, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)
        
        saved_hotkeys = saved_state.get("hotkeys", {})
        if not saved_hotkeys:
            logger.info("No hotkeys found in saved state")
            return {"success": True, "restored_count": 0, "message": "No hotkeys in saved state"}
        
        # Восстанавливаем каждый хоткей
        from mcp_server.tools.lng_winapi.hotkey_listener.hotkey_core import register_hotkey
        restored_count = 0
        failed_count = 0
        
        for hotkey_str, hotkey_data in saved_hotkeys.items():
            try:
                tool_name = hotkey_data.get("tool_name")
                tool_json = hotkey_data.get("tool_json")
                
                if tool_name and tool_json:
                    result = await register_hotkey(hotkey_str, tool_name, tool_json)
                    if result.get("success"):
                        restored_count += 1
                        logger.info(f"Restored hotkey: {hotkey_str}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to restore hotkey {hotkey_str}: {result.get('error')}")
                else:
                    failed_count += 1
                    logger.warning(f"Invalid hotkey data for {hotkey_str}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error restoring hotkey {hotkey_str}: {e}")
        
        logger.info(f"Hotkeys restoration completed: {restored_count} restored, {failed_count} failed")
        return {
            "success": True, 
            "restored_count": restored_count, 
            "failed_count": failed_count,
            "message": f"Restored {restored_count} hotkeys, {failed_count} failed"
        }
        
    except Exception as e:
        logger.error(f"Error restoring hotkeys state: {e}")
        return {"success": False, "error": f"Restoration error: {str(e)}"}

async def tool_info() -> dict:
    return {
        "description": """Manages system-wide hotkeys that call MCP tools when pressed.

This tool provides fast, direct access to Windows hotkey registration:
• Register global hotkeys that work across all applications
• Automatically trigger other MCP tools when hotkeys are pressed
• Manage multiple hotkey listeners simultaneously
• Fast response times with direct Windows API access

**Hotkey Format:**
• Single keys: 'f1', 'f12', 'space', 'enter'
• With modifiers: 'ctrl+f1', 'ctrl+shift+s', 'alt+tab'
• Supported modifiers: ctrl/control, shift, alt, win/windows
• Supported keys: a-z, 0-9, f1-f12, space, enter, tab, esc, etc.

**Operations:**
• 'service_status': Check current status and active hotkeys
• 'register': Register a new hotkey listener (with conflict detection)
• 'unregister': Remove a specific hotkey listener
• 'list': List all active hotkey listeners
• 'unregister_all': Remove all hotkey listeners
• 'restore': Manually restore hotkeys from saved state file

**Persistence:**
• Hotkeys are automatically saved to file when registered/unregistered
• Saved hotkeys are automatically restored on first service access
• Manual restoration available with 'restore' operation

**Error Handling:**
• Detects hotkey conflicts with other applications
• Suggests alternative hotkey combinations
• Shows list of currently registered hotkeys

**Examples:**
Check status: operation="service_status"
Register: operation="register", hotkey="ctrl+shift+f1", tool_name="lng_count_words", tool_json={"input_text": "test"}
List: operation="list"
Unregister: operation="unregister", hotkey="ctrl+shift+f1"
""",
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["service_status", "register", "unregister", "list", "unregister_all"],
                    "description": "Operation to perform"
                },
                "hotkey": {
                    "type": "string",
                    "description": "Hotkey combination (e.g., 'ctrl+shift+f1', 'alt+space'). Required for register/unregister."
                },
                "tool_name": {
                    "type": "string", 
                    "description": "Name of the MCP tool to call when hotkey is pressed. Required for register."
                },
                "tool_json": {
                    "type": "object",
                    "description": "JSON parameters to pass to the tool. Required for register."
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, arguments: dict) -> list[types.Content]:
    operation = arguments.get("operation")
    hotkey = arguments.get("hotkey", "").strip()
    tool_name = arguments.get("tool_name", "").strip()
    tool_json = arguments.get("tool_json", {})
    
    # Все операции работают через быстрый режим
    return await run_tool_fast_mode(operation, hotkey, tool_name, tool_json)

async def run_service_command(service_script: Path, args: list) -> dict:
    """Выполняет команду к hotkey service и возвращает результат"""
    try:
        # Используем правильный путь к Python из виртуальной среды
        python_exe = Path(__file__).parent.parent.parent.parent.parent / ".virtualenv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = sys.executable  # Fallback
        
        cmd = [str(python_exe), str(service_script)] + args
        logger.info(f"Executing service command: {cmd}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Запускаем команду синхронно для простых команд (status, list, etc.)
        logger.info(f"About to run subprocess with timeout=5")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,  # Уменьшаем таймаут до 5 секунд для быстрого ответа
            cwd=Path(__file__).parent.parent.parent.parent.parent  # Устанавливаем рабочую директорию в корень проекта
        )
        logger.info(f"Subprocess completed with returncode: {result.returncode}")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                logger.info(f"Service command result: {response_data}")
                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse service response: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response from service: {result.stdout}"
                }
        else:
            error_msg = result.stderr if result.stderr else f"Command failed with exit code {result.returncode}"
            logger.error(f"Service command failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    except subprocess.TimeoutExpired:
        logger.error("Service command timed out")
        return {
            "success": False,
            "error": "Service command timed out"
        }
    except Exception as e:
        logger.error(f"Error executing service command: {e}")
        return {
            "success": False,
            "error": f"Failed to execute service command: {str(e)}"
        }

def init():
    """Инициализация инструмента - вызывается автоматически при запуске сервера"""
    global _service_initialized
    
    logger.info("Initializing hotkey listener tool...")
    
    try:
        # Запускаем восстановление хоткеев в синхронном режиме для инициализации
        import asyncio
        
        async def async_init():
            # Попытка восстановить сохранённые хоткеи
            restore_result = await restore_hotkeys_state()
            if restore_result.get("success"):
                restored_count = restore_result.get("restored_count", 0)
                if restored_count > 0:
                    logger.info(f"Successfully restored {restored_count} hotkeys during initialization")
                else:
                    logger.info("No hotkeys to restore during initialization")
            else:
                logger.warning(f"Failed to restore hotkeys during initialization: {restore_result.get('error')}")
            
            # Устанавливаем флаг инициализации
            global _service_initialized
            _service_initialized = True
            logger.info("Hotkey listener tool initialization completed")
        
        # Если мы уже в asyncio loop, просто планируем выполнение
        try:
            loop = asyncio.get_running_loop()
            # Создаем задачу для выполнения в текущем loop
            loop.create_task(async_init())
            logger.info("Scheduled hotkey restoration task in existing event loop")
        except RuntimeError:
            # Нет активного loop, создаём новый
            asyncio.run(async_init())
            logger.info("Completed hotkey restoration in new event loop")
            
    except Exception as e:
        logger.error(f"Error during hotkey listener initialization: {e}")
        # Не прерываем инициализацию при ошибке
        _service_initialized = True
