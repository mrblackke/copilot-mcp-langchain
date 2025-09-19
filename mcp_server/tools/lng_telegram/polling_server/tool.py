"""
Telegram Polling Server - универсальный инструмент для создания Telegram ботов
"""

import asyncio
import json
import uuid
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import mcp.types as types
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from mcp_server.logging_config import setup_instance_logger, close_instance_logger
from mcp_server.tools.tool_registry import run_tool as execute_tool
from mcp_server.pipeline.expressions import substitute_expressions

# Логгер будет создаваться только при запуске бота
logger = None

def load_pipeline_from_file(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """Load pipeline configuration from JSON file."""
    try:
        if not os.path.isabs(file_path):
            # Convert relative path to absolute
            file_path = os.path.abspath(file_path)
        
        if logger:
            logger.info(f"Loading pipeline from file: {file_path}")
            logger.info(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            if logger:
                logger.error(f"Pipeline file not found: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Expect pipeline to be in the config
        pipeline = config.get('pipeline', [])
        if logger:
            logger.info(f"Loaded pipeline with {len(pipeline)} steps")
        return pipeline
    except Exception as e:
        if logger:
            logger.error(f"Error loading pipeline from file {file_path}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def tool_info() -> dict:
    """Returns information about the lng_telegram_polling_server tool."""
    return {
        "description": "Telegram Polling Server - универсальный инструмент для работы с Telegram ботами",
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["start", "stop", "status", "send_message"],
                    "description": "Operation to perform"
                },
                "bot_token": {
                    "type": "string",
                    "description": "Telegram bot token (required for start operation)"
                },
                "user_id": {
                    "type": "integer",
                    "description": "User ID for sending messages"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send"
                },
                "pipeline": {
                    "type": "array",
                    "description": "Pipeline to execute on message received",
                    "items": {
                        "type": "object"
                    }
                },
                "pipeline_file": {
                    "type": "string",
                    "description": "Path to JSON file containing pipeline configuration (alternative to pipeline parameter)"
                },
                "bot_name": {
                    "type": "string",
                    "description": "Name of the bot instance (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Executes the Telegram polling server tool."""
    try:
        result = tool_lng_telegram_polling_server(**parameters)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    except Exception as e:
        error_result = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]

class TelegramPollingServer:
    """Сервер для управления Telegram ботом в polling режиме"""
    
    def __init__(self, token: str, pipeline: List[Dict] = None, pipeline_file: str = None):
        global logger
        # Создаем логгер только при создании экземпляра бота
        logger = setup_instance_logger("polling_server", "telegram")
        self.logger = logger
        
        self.token = token
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
        # Сохраняем оригинальный pipeline БЕЗ обработки выражений
        self.pipeline = pipeline or []
        self.pipeline_file = pipeline_file  # Сохраняем путь к файлу пайплайна
        self.running = False
        
        # Настройка обработчиков
        self._setup_handlers()
        
        # Настройка обработчика ошибок
        self._setup_error_handlers()
        
    def _setup_error_handlers(self):
        """Настройка обработчиков ошибок"""
        try:
            # Патчим sys.stderr ДО создания telegram приложения
            import sys
            import io
            
            class TelegramStderrInterceptor:
                def __init__(self, original_stderr, logger):
                    self.original_stderr = original_stderr
                    self.logger = logger
                    self.buffer = ""
                    
                def write(self, text):
                    if text and text.strip():
                        # Записываем ВСЕ в лог файл
                        self.logger.error(f"STDERR: {text.rstrip()}")
                        
                def flush(self):
                    pass
                    
                def fileno(self):
                    return self.original_stderr.fileno()
                    
                def isatty(self):
                    return False
            
            # Заменяем stderr ПОЛНОСТЬЮ
            if not hasattr(sys.stderr, '_intercepted'):
                original_stderr = sys.stderr
                sys.stderr = TelegramStderrInterceptor(original_stderr, self.logger)
                sys.stderr._intercepted = True
                self.logger.info("Stderr fully intercepted")
            
            # Добавляем error handler для telegram-bot
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Обработчик всех ошибок telegram-bot"""
                try:
                    import traceback
                    
                    # Логируем основную ошибку
                    self.logger.error(f"Telegram bot error: {context.error}")
                    
                    # Полный traceback
                    if hasattr(context.error, '__traceback__'):
                        tb_str = ''.join(traceback.format_exception(
                            type(context.error), 
                            context.error, 
                            context.error.__traceback__
                        ))
                        self.logger.error(f"Full traceback:\n{tb_str}")
                        
                    # Логируем детали update если есть
                    if update:
                        self.logger.error(f"Update that caused error: {update}")
                        
                except Exception as log_error:
                    self.logger.error(f"Error in error_handler itself: {log_error}")
            
            # Регистрируем error handler
            self.application.add_error_handler(error_handler)
            
            # Настраиваем все Python логгеры
            import logging
            
            # Перенаправляем ВСЕ логгеры уровня WARNING и выше в наш файл
            class UniversalLogHandler(logging.Handler):
                def __init__(self, main_logger):
                    super().__init__()
                    self.main_logger = main_logger
                    
                def emit(self, record):
                    try:
                        if record.levelno >= logging.WARNING:
                            msg = self.format(record)
                            self.main_logger.error(f"Logger[{record.name}]: {msg}")
                    except Exception:
                        pass
            
            # Агрессивно перехватываем ВСЕ telegram логгеры
            telegram_loggers = [
                'telegram',
                'telegram.bot',
                'telegram.ext',
                'telegram.ext.application',
                'telegram.ext.updater',
                'telegram._utils.request',
                'urllib3',
                'httpcore',
                'httpx'
            ]
            
            for logger_name in telegram_loggers:
                tel_logger = logging.getLogger(logger_name)
                tel_logger.setLevel(logging.DEBUG)
                
                # Удаляем все существующие handlers
                for handler in tel_logger.handlers[:]:
                    tel_logger.removeHandler(handler)
                
                # Добавляем наш handler
                tel_handler = logging.StreamHandler()
                tel_handler.setLevel(logging.DEBUG)
                tel_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                tel_handler.setFormatter(tel_formatter)
                
                # Перенаправляем в наш логгер
                class TelegramRedirectHandler(logging.Handler):
                    def __init__(self, target_logger):
                        super().__init__()
                        self.target_logger = target_logger
                        
                    def emit(self, record):
                        try:
                            msg = self.format(record)
                            self.target_logger.error(f"TELEGRAM[{record.name}]: {msg}")
                        except Exception:
                            pass
                
                redirect_handler = TelegramRedirectHandler(self.logger)
                redirect_handler.setFormatter(tel_formatter)
                tel_logger.addHandler(redirect_handler)
                tel_logger.propagate = False  # Не передавать в родительские логгеры
                
                self.logger.info(f"Intercepted logger: {logger_name}")
                
            self.logger.info("All telegram loggers intercepted")
            
            # Перехватываем print() функцию для telegram библиотек
            original_print = __builtins__.get('print', print)
            
            def intercepted_print(*args, **kwargs):
                try:
                    # Проверяем есть ли в стеке вызовов telegram модули
                    import inspect
                    frame = inspect.currentframe()
                    while frame:
                        filename = frame.f_code.co_filename
                        if 'telegram' in filename or 'httpx' in filename or 'urllib3' in filename:
                            # Это вызов из telegram библиотеки - перенаправляем в лог
                            message = ' '.join(str(arg) for arg in args)
                            self.logger.error(f"TELEGRAM_PRINT: {message}")
                            return
                        frame = frame.f_back
                    
                    # Обычный print для всех остальных
                    original_print(*args, **kwargs)
                except Exception:
                    # В случае ошибки используем оригинальный print
                    original_print(*args, **kwargs)
            
            # Заменяем print в builtins (безопасно)
            import builtins
            try:
                builtins.print = intercepted_print
                self.logger.info("Print function intercepted for telegram libraries")
            except Exception as print_error:
                self.logger.warning(f"Could not intercept print function: {print_error}")
                # Не критично, продолжаем без перехвата print
            
            # Добавляем universal handler к корневому логгеру
            root_logger = logging.getLogger()
            universal_handler = UniversalLogHandler(self.logger)
            universal_handler.setLevel(logging.WARNING)
            
            # Убираем все stderr handlers с корневого логгера
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler):
                    root_logger.removeHandler(handler)
                    
            root_logger.addHandler(universal_handler)
            
            self.logger.info("All error handlers configured - stderr and logging intercepted")
            
        except Exception as e:
            self.logger.error(f"Failed to setup error handlers: {e}")
            import traceback
            self.logger.error(f"Setup error traceback: {traceback.format_exc()}")
        
    def _setup_handlers(self):
        """Настройка обработчиков сообщений"""
        self.application.add_handler(CommandHandler("start", self._handle_start))
        # Обрабатываем все текстовые сообщения, включая команды /tamam и /cancel
        self.application.add_handler(MessageHandler(filters.TEXT, self._handle_message))
        
    def close_logger(self):
        """Закрытие логгера и освобождение файловых дескрипторов"""
        if hasattr(self, 'logger') and self.logger:
            close_instance_logger("polling_server", "telegram")
            self.logger = None
        
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Получаем параметр сессии из deep link
            session_id = None
            if context.args:
                session_id = context.args[0]
                
            logger.info(f"User {user_id} started bot with session_id: {session_id}")
            
            # Выполняем pipeline для команды start
            start_text = f"/start{' ' + session_id if session_id else ''}"
            await self._process_message_pipeline(user_id, start_text, update)
                
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await update.message.reply_text("Произошла ошибка при подключении к боту")
            
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # Пропускаем команду /start, так как она обрабатывается отдельно
            if message_text.startswith("/start"):
                return
            
            logger.info(f"Message from {user_id}: {message_text}")
            
            # Выполняем pipeline для обработки сообщения
            await self._process_message_pipeline(user_id, message_text, update)
            
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            await update.message.reply_text("Произошла ошибка при обработке сообщения")
            
    async def _process_message_pipeline(self, user_id: int, message_text: str, update: Update):
        """Обработка сообщения через pipeline с автоматической отправкой ответов"""
        try:
            # Подготавливаем базовый контекст для pipeline
            user = update.effective_user
            telegram_context = {
                "user_id": user_id,
                "message": message_text,
                "username": user.username or "",
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "language_code": user.language_code or "en",
                "is_bot": user.is_bot,
                "update_id": update.update_id,
                "chat_id": update.effective_chat.id,
                "chat_type": update.effective_chat.type,
                "message_id": update.message.message_id,
                "timestamp": update.message.date.isoformat() if update.message.date else None
            }
            
            context = {
                "telegram_context": telegram_context,
                "telegram": telegram_context  # Алиас для совместимости
            }
            
            # Определяем какой pipeline использовать
            current_pipeline = self.pipeline
            
            # Если указан pipeline_file, загружаем его при каждом сообщении
            # чтобы можно было использовать telegram контекст
            if self.pipeline_file:
                loaded_pipeline = load_pipeline_from_file(self.pipeline_file)
                if loaded_pipeline:
                    current_pipeline = loaded_pipeline
                else:
                    logger.error(f"Failed to load pipeline from file: {self.pipeline_file}")
                    current_pipeline = self.pipeline  # Fallback на исходный pipeline
            
            # Выполняем pipeline если он задан
            pipeline_results = []
            if current_pipeline:
                for step in current_pipeline:
                    tool_name = step.get("tool")
                    tool_params = step.get("params", {})
                    
                    # Подставляем контекст в параметры
                    processed_params = self._substitute_context(tool_params, context)
                    
                    try:
                        # Выполняем инструмент через импорт модуля
                        result = await self._execute_tool(tool_name, processed_params)
                        
                        logger.info(f"Pipeline step {tool_name} executed successfully")
                        
                        # Сохраняем результат в контекст
                        output_var = step.get("output")
                        if output_var:
                            context[output_var] = result
                            
                        pipeline_results.append({
                            "tool": tool_name,
                            "result": result,
                            "success": True
                        })
                        
                        # Проверяем результат на наличие response для автоотправки
                        await self._handle_tool_response(result, user_id, update)
                            
                    except Exception as e:
                        error_msg = f"Error executing pipeline step {tool_name}: {e}"
                        logger.error(error_msg)
                        
                        pipeline_results.append({
                            "tool": tool_name,
                            "error": str(e),
                            "success": False
                        })
                        
                        # Отправляем сообщение об ошибке пользователю
                        await update.message.reply_text("Произошла ошибка при обработке сообщения")
                        
            # Сохраняем результаты pipeline в контекст
            context["pipeline_results"] = pipeline_results
                        
        except Exception as e:
            logger.error(f"Error in message pipeline: {e}")
            await update.message.reply_text("Произошла ошибка в системе обработки сообщений")
            
    async def _execute_tool(self, tool_name: str, params: dict) -> dict:
        """Выполнение инструмента через tool_registry (как в lng_batch_run)"""
        try:
            logger.info(f"Executing tool {tool_name} with params: {params}")
            
            # Используем импортированный execute_tool (то же что в lng_batch_run)
            result = await execute_tool(tool_name, params)
            
            # Парсим результат из TextContent если нужно
            if isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                if hasattr(first_result, 'text'):
                    import json
                    try:
                        parsed_result = json.loads(first_result.text)
                        return parsed_result
                    except json.JSONDecodeError:
                        return {"response": first_result.text}
                else:
                    return first_result
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}")
            import traceback
            logger.error(f"Tool execution traceback: {traceback.format_exc()}")
            raise
            
    async def _handle_tool_response(self, result: dict, user_id: int, update: Update):
        """Обработка результата инструмента для автоматической отправки ответов"""
        try:
            # Проверяем различные варианты ответов в результате
            response_text = None
            
            # Вариант 1: прямое поле response
            if isinstance(result, dict):
                if "response" in result:
                    response_text = result["response"]
                elif "reply" in result:
                    response_text = result["reply"]
                elif "message" in result:
                    response_text = result["message"]
                elif "improved" in result and "original" in result:
                    # Специально для super_empath - форматируем ответ
                    original = result["original"]
                    improved = result["improved"]
                    response_text = f"""📝 **Ваше сообщение:**
"{original}"

💡 **Предлагаю переформулировать:**
"{improved}"

Напишите "тамам" для отправки или "отбой" для отмены."""
            
            # Отправляем ответ если он есть
            if response_text and isinstance(response_text, str) and response_text.strip():
                # Логируем что отправляем
                logger.info(f"Sending message to user {user_id}: {repr(response_text)}")
                await update.message.reply_text(response_text)  # Убрали parse_mode='Markdown'
                logger.info(f"Auto-sent response to user {user_id}")
                
            # Проверяем auto_send для отправки сообщений другим пользователям
            if isinstance(result, dict) and "auto_send" in result:
                auto_send = result["auto_send"]
                if isinstance(auto_send, dict):
                    to_users = auto_send.get("to_users", [])
                    message_text = auto_send.get("message", "")
                    
                    if to_users and message_text:
                        sent_count = 0
                        for target_user_id in to_users:
                            try:
                                # Логируем что отправляем
                                logger.info(f"Auto-sending message to user {target_user_id}: {repr(message_text)}")
                                await self.bot.send_message(
                                    chat_id=target_user_id,
                                    text=message_text
                                )  # Убрали parse_mode='Markdown'
                                sent_count += 1
                                logger.info(f"Auto-sent message to user {target_user_id}")
                            except Exception as e:
                                logger.error(f"Failed to auto-send message to user {target_user_id}: {e}")
                        
                        logger.info(f"Auto-sent messages to {sent_count}/{len(to_users)} users")
                
        except Exception as e:
            logger.error(f"Error handling tool response: {e}")
            
    def _substitute_context(self, params: Dict, context: Dict) -> Dict:
        """Подстановка контекста в параметры используя expressions.py"""
        try:
            # Используем substitute_expressions как в других инструментах
            return self._substitute_variables(params, context)
        except Exception as e:
            logger.error(f"Error in context substitution: {e}")
            return params
            
    def _substitute_variables(self, obj: Any, context: dict) -> Any:
        """Substitute variables in response template using new expression system."""
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, context) for item in obj]
        elif isinstance(obj, str) and ("{!" in obj or "[!" in obj):
            try:
                return substitute_expressions(obj, context, expected_result_type="python")
            except Exception as e:
                logger.warning(f"Variable substitution failed for '{obj}': {e}")
                return obj
        else:
            return obj

# Глобальные именованные экземпляры серверов
_server_instances: Dict[str, TelegramPollingServer] = {}

async def start_polling_server(token: str, pipeline: List[Dict] = None, bot_name: str = "default") -> TelegramPollingServer:
    """Запуск polling сервера"""
    global _server_instances
    
    # Если бот с таким именем уже запущен, останавливаем его
    if bot_name in _server_instances and _server_instances[bot_name].running:
        logger.info(f"Stopping existing bot '{bot_name}' before starting new one")
        await stop_polling_server(bot_name)
    
    # Небольшая пауза для корректной остановки
    import asyncio
    await asyncio.sleep(0.5)
        
    _server_instances[bot_name] = TelegramPollingServer(token, pipeline)
    _server_instances[bot_name].running = True
    
    logger.info(f"Starting Telegram polling server '{bot_name}'...")
    await _server_instances[bot_name].application.run_polling()
    
    return _server_instances[bot_name]

async def stop_polling_server(bot_name: str = "default"):
    """Остановка polling сервера"""
    global _server_instances
    
    if bot_name in _server_instances and _server_instances[bot_name].running:
        logger.info(f"Stopping Telegram polling server '{bot_name}'...")
        await _server_instances[bot_name].application.stop()
        _server_instances[bot_name].running = False
        _server_instances[bot_name].close_logger()
        del _server_instances[bot_name]
    else:
        logger.warning(f"Bot '{bot_name}' is not running")

async def send_message(user_id: int, text: str, bot_name: str = "default") -> bool:
    """Отправка сообщения пользователю"""
    global _server_instances
    
    if bot_name not in _server_instances:
        logger.error(f"Polling server '{bot_name}' not running")
        return False
        
    try:
        await _server_instances[bot_name].bot.send_message(user_id, text)
        return True
    except TelegramError as e:
        logger.error(f"Error sending message to {user_id}: {e}")
        return False



def get_server_status(bot_name: str = "default") -> Dict:
    """Получение статуса сервера"""
    global _server_instances
    
    if bot_name not in _server_instances:
        return {"running": False, "pipeline_count": 0}
    
    # Определяем правильное количество шагов pipeline
    pipeline_count = len(_server_instances[bot_name].pipeline)
    if _server_instances[bot_name].pipeline_file and pipeline_count == 0:
        file_pipeline = load_pipeline_from_file(_server_instances[bot_name].pipeline_file)
        if file_pipeline:
            pipeline_count = len(file_pipeline)
        
    return {
        "running": _server_instances[bot_name].running,
        "pipeline_count": pipeline_count,
        "pipeline_source": "file" if _server_instances[bot_name].pipeline_file else "inline"
    }

def tool_lng_telegram_polling_server(
    operation: str,
    token: str = None,
    user_id: int = None,
    message: str = None,
    pipeline: List[Dict] = None,
    pipeline_file: str = None,
    bot_name: str = "default"
) -> Dict[str, Any]:
    """
    Telegram Polling Server - универсальный инструмент для работы с Telegram ботами
    
    Operations:
    - start: Запуск polling сервера (запускается в фоновом режиме)
    - stop: Остановка сервера  
    - send_message: Отправка сообщения пользователю
    - status: Получение статуса сервера
    """
    
    global _server_instances
    
    # Обработка pipeline_file если указан - НЕ обрабатываем на этапе запуска
    # pipeline_file будет обработан при создании экземпляра TelegramPollingServer
    loaded_pipeline_file = pipeline_file
    
    try:
        if operation == "start":
            if not token:
                # Пытаемся получить токен из .env
                from dotenv import load_dotenv
                load_dotenv()
                token = os.getenv("TELEGRAM_BOT_TOKEN")
                
                if not token:
                    return {"error": "Token is required for start operation"}
            
            # Простая проверка валидности токена
            if ":" not in token or len(token.split(":")) != 2:
                return {"error": "Invalid bot token format"}
            
            # Запуск бота с pipeline поддержкой
            if bot_name in _server_instances and _server_instances[bot_name].running:
                return {"error": f"Server '{bot_name}' already running"}
            
            # Принудительная очистка перед запуском
            if bot_name in _server_instances:
                try:
                    _server_instances[bot_name].close_logger()
                except:
                    pass
                del _server_instances[bot_name]
            
            try:
                import asyncio
                import threading
                import time
                
                def run_bot():
                    global _server_instances, logger
                    
                    # Создаем полностью новый event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Перенаправляем stderr в логгер
                        import sys
                        import io
                        
                        class LoggerWriter:
                            def __init__(self, logger, level):
                                self.logger = logger
                                self.level = level
                                
                            def write(self, message):
                                if message.strip():  # Игнорируем пустые строки
                                    # Фильтруем telegram ошибки
                                    if any(keyword in message for keyword in [
                                        'telegram.error',
                                        'Conflict: terminated by other getUpdates',
                                        'PTBUserWarning',
                                        'No error handlers are registered'
                                    ]):
                                        if hasattr(self, 'logger') and self.logger:
                                            self.logger.error(f"Telegram: {message.strip()}")
                                    
                            def flush(self):
                                pass
                        
                        # Создаем новый экземпляр сервера
                        _server_instances[bot_name] = TelegramPollingServer(token, pipeline or [], loaded_pipeline_file)
                        _server_instances[bot_name].running = True
                        
                        # Обновляем глобальный логгер
                        logger = _server_instances[bot_name].logger
                        logger.info(f"Starting Telegram polling server '{bot_name}'...")
                        
                        # Перенаправляем stderr
                        original_stderr = sys.stderr
                        sys.stderr = LoggerWriter(logger, 'error')
                        
                        try:
                            # Запускаем polling
                            _server_instances[bot_name].application.run_polling(
                                close_loop=False,  # Не закрываем loop автоматически
                                stop_signals=None  # Отключаем обработку сигналов
                            )
                        finally:
                            # Восстанавливаем stderr
                            sys.stderr = original_stderr
                        
                    except Exception as e:
                        if logger:
                            logger.error(f"Bot error: {e}")
                        if bot_name in _server_instances:
                            _server_instances[bot_name].running = False
                    finally:
                        # Принудительная очистка loop
                        try:
                            pending = asyncio.all_tasks(loop)
                            for task in pending:
                                task.cancel()
                            if pending:
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except:
                            pass
                        loop.close()
                
                # Запускаем в отдельном потоке
                bot_thread = threading.Thread(target=run_bot, daemon=True)
                bot_thread.start()
                
                # Небольшая задержка для инициализации
                time.sleep(0.5)
                
                # Определяем правильное количество шагов pipeline
                pipeline_count = 0
                if pipeline:
                    pipeline_count = len(pipeline)
                elif loaded_pipeline_file:
                    file_pipeline = load_pipeline_from_file(loaded_pipeline_file)
                    if file_pipeline:
                        pipeline_count = len(file_pipeline)
                
                return {
                    "status": "started",
                    "message": "Telegram bot started with pipeline support",
                    "pipeline_count": pipeline_count,
                    "pipeline_source": "inline" if pipeline else ("file" if loaded_pipeline_file else "none")
                }
                
            except Exception as e:
                return {"error": f"Failed to start bot: {str(e)}"}
                
        elif operation == "stop":
            if bot_name in _server_instances and _server_instances[bot_name].running:
                try:
                    logger.info(f"Stopping Telegram polling server '{bot_name}'...")
                    _server_instances[bot_name].running = False
                    
                    if _server_instances[bot_name].application:
                        # Более тщательная остановка
                        import asyncio
                        import threading
                        import time
                        
                        def stop_bot():
                            try:
                                # Создаем новый event loop для остановки
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                # Останавливаем приложение
                                loop.run_until_complete(_server_instances[bot_name].application.stop())
                                
                                # Дополнительная очистка
                                if hasattr(_server_instances[bot_name].application, 'updater'):
                                    loop.run_until_complete(_server_instances[bot_name].application.updater.stop())
                                
                                # Закрываем все задачи
                                pending = asyncio.all_tasks(loop)
                                for task in pending:
                                    task.cancel()
                                
                                if pending:
                                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                                    
                            except Exception as e:
                                logger.error(f"Error stopping bot: {e}")
                            finally:
                                loop.close()
                        
                        # Запускаем остановку в отдельном потоке
                        stop_thread = threading.Thread(target=stop_bot, daemon=True)
                        stop_thread.start()
                        stop_thread.join(timeout=10)  # Увеличили timeout
                        
                        # Принудительно очищаем ссылку на приложение
                        _server_instances[bot_name].application = None
                    
                    # Закрываем логгер
                    _server_instances[bot_name].close_logger()
                    
                    # Очищаем глобальную ссылку
                    del _server_instances[bot_name]
                    
                    return {"status": "stopped", "message": f"Telegram bot '{bot_name}' stopped"}
                except Exception as e:
                    return {"error": f"Failed to stop bot: {str(e)}"}
            else:
                return {"status": "not_running", "message": "Bot is not running"}
            
        elif operation == "send_message":
            if not user_id or not message:
                return {"error": "user_id and message are required"}
            
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(send_message(user_id, message, bot_name))
                return {
                    "status": "sent" if success else "failed",
                    "user_id": user_id,
                    "message": message
                }
            except Exception as e:
                return {"error": f"Failed to send message: {str(e)}"}
            
        elif operation == "status":
            return get_server_status(bot_name)
            
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        logger.error(f"Error in telegram polling server: {e}")
        return {"error": str(e)}
