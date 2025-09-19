"""
Super Empath - бизнес-логика эмоционального переводчика для улучшения коммуникации в отношениях
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any

import mcp.types as types

from mcp_server.logging_config import setup_instance_logger, close_instance_logger

# Логгер будет создан при первом использовании
logger = setup_instance_logger("super_empath", "telegram")

async def tool_info() -> dict:
    """Returns information about the lng_telegram_super_empath tool."""
    return {
        "description": "Super Empath - бизнес-логика эмоционального переводчика для улучшения коммуникации в отношениях",
        "schema": {
            "type": "object",
            "properties": {
                "telegram_context": {
                    "type": "string",
                    "description": "Telegram context JSON string with user and message information"
                },
                "prompt_template_name": {
                    "type": "string",
                    "description": "Name of the prompt template to use for LLM processing",
                    "default": "default_super_empath"
                }
            },
            "required": ["telegram_context"]
        }
    }

class SuperEmpathProcessor:
    """Процессор Super Empath для обработки сообщений"""
    
    def __init__(self):
        self.session_file = "mcp_server/config/telegram/super_empath_sessions.json"
        self._ensure_session_file()
        
    def _ensure_session_file(self):
        """Убеждаемся что файл сессий существует"""
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        if not os.path.exists(self.session_file):
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump({"sessions": {}, "users": {}}, f)
                
    def _load_sessions(self) -> dict:
        """Загрузка сессий из файла"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"sessions": {}, "users": {}}
            
    def _save_sessions(self, data: dict):
        """Сохранение сессий в файл"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
            
    async def improve_message_with_llm(self, message: str, user_id: str, template_name: str = "default_super_empath") -> dict:
        """Улучшение сообщения через LLM с использованием истории сессии"""
        try:
            # Загружаем историю сессии для пользователя
            conversation_history = self._get_conversation_history(user_id)
            
            # Импортируем необходимые модули для обращения к LLM
            from mcp_server.tools.tool_registry import run_tool as execute_tool
            
            # Выполняем LLM prompt template
            llm_params = {
                "command": "use",
                "template_name": template_name,
                "conversation_history": conversation_history,
                "user_message": message,
                "user_id": user_id
            }
            
            result_content = await execute_tool("lng_llm_prompt_template", llm_params)
            
            if result_content and len(result_content) > 0:
                result_text = result_content[0].text
                # Парсим JSON ответ от LLM
                import json
                llm_response = json.loads(result_text)
                
                logger.info(f"LLM response for user {user_id}: {llm_response}")
                
                return {
                    "explanation": llm_response.get("explanation", ""),
                    "suggestion": llm_response.get("suggestion", message),
                    "success": True
                }
            else:
                logger.error("Empty response from LLM")
                return {
                    "explanation": "Не удалось получить ответ от LLM",
                    "suggestion": message,
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in improve_message_with_llm: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Возвращаем fallback в случае ошибки
            return {
                "explanation": f"Произошла ошибка при обработке сообщения: {e}",
                "suggestion": message,
                "success": False
            }
    
    def _get_conversation_history(self, user_id: str) -> str:
        """Получение истории сообщений пользователя из правильной структуры папок"""
        try:
            # Получаем session_id для пользователя
            data = self._load_sessions()
            user_data = data["users"].get(str(user_id))
            
            if not user_data:
                return "История сообщений пуста."
                
            session_id = user_data.get("session_id")
            if not session_id:
                return "История сообщений пуста."
                
            # Путь к файлу истории: sessions/<SESSION_ID>/<USER_ID>.txt
            history_dir = f"mcp_server/config/telegram/sessions/{session_id}"
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = f"{history_dir}/{user_id}.txt"
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "История сообщений пуста."
                
        except Exception as e:
            logger.error(f"Error reading conversation history for user {user_id}: {e}")
            return "Ошибка при загрузке истории сообщений."
    
    def _save_to_history(self, user_id: str, emoji: str, label: str, message: str, session_id: str = None, timestamp: bool = True):
        """Универсальное сохранение любого типа сообщения в историю"""
        try:
            # Получаем session_id если не передан
            if not session_id:
                data = self._load_sessions()
                user_data = data["users"].get(str(user_id))
                if user_data:
                    session_id = user_data.get("session_id")
                    
            if not session_id:
                logger.error(f"No session_id found for user {user_id}")
                return
                
            # Создаем структуру папок: sessions/<SESSION_ID>/<USER_ID>.txt
            history_dir = f"mcp_server/config/telegram/sessions/{session_id}"
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = f"{history_dir}/{user_id}.txt"
            
            # Формат: {emoji}[{label}] (timestamp): {message}
            if timestamp:
                timestamp_str = f" ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            else:
                timestamp_str = ""
            
            history_entry = f"{emoji}[{label}]{timestamp_str}: {message}\n"
            
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(history_entry)
                
            logger.info(f"Saved message to history for user {user_id} in session {session_id}: {emoji}[{label}]")
            
        except Exception as e:
            logger.error(f"Error saving message to history for user {user_id}: {e}")

    # Удобные методы-обертки для разных типов сообщений
    def _save_message_to_history(self, user_id: str, user_name: str, message: str, session_id: str = None):
        """Сохранение обычного сообщения пользователя"""
        self._save_to_history(user_id, "💬", f"{user_id}|{user_name}", message, session_id)
    
    def _save_empath_message_to_history(self, user_id: str, message: str, session_id: str = None):
        """Сохранение рекомендации ассистента"""
        self._save_to_history(user_id, "💡🤖", "EMPATH", message, session_id)
    
    def _save_empath_sent_message_to_history(self, user_id: str, message: str, session_id: str = None):
        """Сохранение отправленного ассистентом сообщения"""
        self._save_to_history(user_id, "⬅️🤖", "EMPATH", message, session_id)
    
    def _save_incoming_message_to_history(self, user_id: str, sender_id: str, sender_name: str, message: str, session_id: str = None):
        """Сохранение входящего сообщения от другого участника"""
        self._save_to_history(user_id, "➡️", f"{sender_id}|{sender_name}", message, session_id)
    
    def _save_system_message_to_history(self, user_id: str, user_name: str, message: str, session_id: str = None):
        """Сохранение системного сообщения"""
        self._save_to_history(user_id, "⚙️", "СИСТЕМА", message, session_id)
    
    def _save_command_to_history(self, user_id: str, user_name: str, command: str, emoji: str, session_id: str = None):
        """Сохранение команды (✅ /tamam, ❌ /cancel)"""
        self._save_to_history(user_id, emoji, f"{user_id}|{user_name}", command, session_id)

        
    async def handle_command(self, telegram_context: dict) -> dict:
        """Обработка команд Super Empath"""
        # Извлекаем текст из объекта message
        message_obj = telegram_context.get("message", {})
        if isinstance(message_obj, dict):
            message = message_obj.get("text", "").strip()
        else:
            message = str(message_obj).strip()
        user_id = telegram_context.get("user_id")
        
        # Проверяем, зарегистрирован ли пользователь
        data = self._load_sessions()
        user_data = data["users"].get(str(user_id))
        
        if message.startswith("/start"):
            return self._handle_start_command(telegram_context)
        elif message == "/tamam":
            return self._handle_approve_command(telegram_context)
        elif message == "/cancel":
            return self._handle_cancel_command(telegram_context)
        elif not user_data:
            # Пользователь не зарегистрирован - показываем приветствие
            return self._handle_welcome_message(telegram_context)
        else:
            return await self._handle_regular_message(telegram_context)
            
    def _handle_welcome_message(self, telegram_context: dict) -> dict:
        """Показ приветственного сообщения для незарегистрированных пользователей"""
        first_name = telegram_context.get("first_name", "Пользователь")
        # Извлекаем текст из объекта message
        message_obj = telegram_context.get("message", {})
        if isinstance(message_obj, dict):
            message = message_obj.get("text", "").strip()
        else:
            message = str(message_obj).strip()
        
        # Проверяем, это deep link или обычное сообщение
        session_id = None
        if " " in message:
            parts = message.split(" ", 1)
            if len(parts) > 1:
                session_id = parts[1]
        
        # Если есть session_id, показываем приветствие для присоединения
        is_joining = session_id is not None
        
        welcome_text = self._get_welcome_message(first_name, is_joining_session=is_joining)
        
        return {
            "response": welcome_text,
            "action": "welcome_shown"
        }
            
    def _get_welcome_message(self, first_name: str, is_joining_session: bool = False, session_id: str = None) -> str:
        """Генерирует приветственное сообщение с общим шаблоном"""
                
        base_message = f"""🎯 Добро пожаловать, {first_name}!

Если вы тут - вы хотите наладить отношения.

Каждое сообщение отправленное вами будет проходить эмоциональную и экономичную модерацию. Вы сможете поговорить через Медиатора с вашими собеседниками. Возражайте, давайте ему больше контекста и вы вместе подберете наилучшую реализацию.

Только если вы скажете /tamam оно уйдет всем собеседникам. Если же вы скажете /cancel оно будет забыто.

Ваши собеседники будут так же модерировать свои сообщения перед отправкой их вам.

Удачи в переговорах!"""

        # Только для присоединившихся показываем session_id
        if is_joining_session and session_id:
            specific_part = f"\n\nВы присоединились к сессии: {session_id}"
        else:
            specific_part = ""
        
        return base_message + specific_part

    def _handle_start_command(self, telegram_context: dict) -> dict:
        """Обработка команды /start"""
        user_id = telegram_context.get("user_id")
        first_name = telegram_context.get("first_name", "Пользователь")
        # Извлекаем текст из объекта message
        message_obj = telegram_context.get("message", {})
        if isinstance(message_obj, dict):
            message = message_obj.get("text", "").strip()
        else:
            message = str(message_obj).strip()
        
        # Извлекаем session_id из deep link
        session_id = None
        if " " in message:
            parts = message.split(" ", 1)
            if len(parts) > 1:
                session_id = parts[1]
                
        data = self._load_sessions()
        
        if session_id:
            # Присоединение к существующей сессии
            if session_id in data["sessions"]:
                session = data["sessions"][session_id]
                if user_id not in session["participants"]:
                    session["participants"].append(user_id)
                    session["last_activity"] = datetime.now().isoformat()
                    
                data["users"][str(user_id)] = {
                    "session_id": session_id,
                    "first_name": first_name,
                    "joined_at": datetime.now().isoformat()
                }
                
                self._save_sessions(data)
                
                # Создаем файл истории для присоединившегося участника
                self._save_system_message_to_history(user_id, first_name, f"Присоединился к сессии {session_id}", session_id)
                
                # Отправляем приветственное сообщение для присоединившегося
                welcome_message = self._get_welcome_message(first_name, is_joining_session=True, session_id=session_id)
                
                return {
                    "response": welcome_message,
                    "session_id": session_id,
                    "action": "joined_session"
                }
            else:
                return {
                    "response": "❌ Сессия не найдена. Попросите новую ссылку-приглашение.",
                    "action": "session_not_found"
                }
        else:
            # Создание новой сессии
            new_session_id = str(uuid.uuid4())[:8]  # Короткий ID для удобства
            
            data["sessions"][new_session_id] = {
                "participants": [user_id],
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "created_by": user_id
            }
            
            data["users"][str(user_id)] = {
                "session_id": new_session_id,
                "first_name": first_name,
                "joined_at": datetime.now().isoformat()
            }
            
            self._save_sessions(data)
            
            # Создаем файл истории для создателя сессии
            self._save_system_message_to_history(user_id, first_name, f"Создал сессию {new_session_id}", new_session_id)
            
            # Отправляем приветственное сообщение для создателя сессии
            welcome_message = self._get_welcome_message(first_name, is_joining_session=False)
            
            # Генерируем ссылку-приглашение (используем реальное имя бота)
            invite_link = f"https://t.me/IStillLoveYou_Bot?start={new_session_id}"
            
            # Логируем что именно генерируем
            logger.info(f"Generated invite link: {invite_link}")
            
            # Комбинируем приветствие с информацией о ссылке (возвращаем эмодзи)
            full_message = f"{welcome_message}\n\n🔗 Ваша ссылка для приглашения собеседников:\n\n{invite_link}\n\nОтправьте эту ссылку тем, кого хотите услышать и если хотите быть услышаны."
            
            return {
                "response": full_message,
                "session_id": new_session_id,
                "invite_link": invite_link,
                "action": "created_session"
            }
            
    async def _handle_regular_message(self, telegram_context: dict) -> dict:
        """Обработка обычного сообщения через LLM"""
        # Извлекаем текст из объекта message
        message_obj = telegram_context.get("message", {})
        if isinstance(message_obj, dict):
            message = message_obj.get("text", "").strip()
        else:
            message = str(message_obj).strip()
        user_id = str(telegram_context.get("user_id"))
        first_name = telegram_context.get("first_name", "Пользователь")
        template_name = telegram_context.get("prompt_template_name", "default_super_empath")
        
        # Проверяем, что пользователь в сессии
        data = self._load_sessions()
        user_data = data["users"].get(str(user_id))
        
        if not user_data:
            return {
                "response": "Пожалуйста, сначала выполните команду /start",
                "action": "not_registered"
            }
        
        # Сохраняем сообщение в историю
        session_id = user_data.get("session_id")
        self._save_message_to_history(user_id, first_name, message, session_id)
        
        # Получаем ответ от LLM
        llm_result = await self.improve_message_with_llm(message, user_id, template_name)
        
        if llm_result["success"]:
            explanation = llm_result["explanation"]
            suggestion = llm_result["suggestion"]
            
            # Сохраняем объяснение и предложение в историю отдельными строками
            self._save_to_history(user_id, "🤔🤖", "EMPATH", explanation, session_id)
            self._save_to_history(user_id, "💡🤖", "EMPATH", f"Предлагаю: {suggestion}", session_id)
            
            # Сохраняем текущее сообщение для последующего одобрения
            user_data["pending_message"] = {
                "original": message,
                "improved": suggestion,
                "explanation": explanation,
                "timestamp": datetime.now().isoformat()
            }
            
            data["users"][str(user_id)] = user_data
            self._save_sessions(data)
            
            response = f"""🤔 {explanation}

💡 Предлагаю: {suggestion}

Напишите ✅ /tamam для отправки или ❌ /cancel для отмены."""
        
        else:
            # В случае ошибки LLM показываем простое сообщение
            error_message = "Простите, сейчас сервис недоступен. Попробуйте позже."
            
            # Сохраняем сообщение об ошибке в историю
            self._save_empath_message_to_history(user_id, "Сервис временно недоступен", session_id)
            
            return {
                "response": error_message,
                "original": message,
                "improved": message,  # возвращаем оригинальное сообщение
                "explanation": llm_result["explanation"],
                "action": "service_unavailable"
            }

        return {
            "response": response,
            "original": message,
            "improved": llm_result.get("suggestion", message),
            "explanation": llm_result.get("explanation", ""),
            "action": "message_processed"
        }
        
    def _handle_approve_command(self, telegram_context: dict) -> dict:
        """Обработка команды одобрения '/tamam'"""
        user_id = telegram_context.get("user_id")
        first_name = telegram_context.get("first_name", "Пользователь")
        
        data = self._load_sessions()
        user_data = data["users"].get(str(user_id))
        
        if not user_data or "pending_message" not in user_data:
            return {
                "response": "⚠️ Вы еще ничего не отправили",
                "action": "no_pending_message"
            }
            
        pending = user_data["pending_message"]
        session_id = user_data["session_id"]
        
        if session_id not in data["sessions"]:
            return {
                "response": "Ошибка: сессия не найдена",
                "action": "session_error"
            }
            
        # Сохраняем команду "/tamam" в историю
        self._save_command_to_history(user_id, first_name, "/tamam", "✅", session_id)
        
        # Сохраняем факт отправки финального сообщения
        final_message = "Отправлено."
        self._save_empath_sent_message_to_history(user_id, final_message, session_id)
        
        session = data["sessions"][session_id]
        participants = session["participants"]
        
        # Логируем входящее сообщение для всех остальных участников сессии
        sender_name = user_data.get("first_name", "Участник")
        other_participants = [p for p in participants if p != user_id]
        
        for participant_id in other_participants:
            try:
                self._save_incoming_message_to_history(
                    str(participant_id), 
                    str(user_id),  # sender_id
                    sender_name, 
                    pending['improved'], 
                    session_id
                )
                logger.info(f"Logged incoming message for participant {participant_id} from {sender_name}")
            except Exception as e:
                logger.error(f"Failed to log incoming message for participant {participant_id}: {e}")
        
        # Очищаем pending message
        del user_data["pending_message"]
        data["users"][str(user_id)] = user_data
        self._save_sessions(data)
        
        # Возвращаем информацию для отправки другим участникам
        other_participants = [p for p in participants if p != user_id]
        
        # Формируем упрощенный ответ
        response_text = f"✅ Сообщение отправлено {len(other_participants)} участникам\n{pending['improved']}"
        
        return {
            "response": response_text,
            "action": "message_approved",
            "improved_message": pending["improved"],
            "original_message": pending["original"],
            "recipients": other_participants,
            "sender_name": user_data.get("first_name", "Участник"),
            # Специальное поле для автоматической обработки транспортным слоем
            "auto_send": {
                "to_users": other_participants,
                "message": f"💬 {user_data.get('first_name', 'Участник')}: {pending['improved']}"
            }
        }
        
    def _handle_cancel_command(self, telegram_context: dict) -> dict:
        """Обработка команды отмены '/cancel'"""
        user_id = telegram_context.get("user_id")
        first_name = telegram_context.get("first_name", "Пользователь")
        
        data = self._load_sessions()
        user_data = data["users"].get(str(user_id))
        
        if not user_data or "pending_message" not in user_data:
            return {
                "response": "⚠️ Вы еще ничего не отправили",
                "action": "no_pending_operation"
            }
        
        session_id = user_data.get("session_id")
        
        # Сохраняем команду "/cancel" в историю
        self._save_command_to_history(user_id, first_name, "/cancel", "❌", session_id)
        
        # Сохраняем факт отмены операции
        self._save_empath_sent_message_to_history(user_id, "Операция отменена", session_id)
            
        # Очищаем pending message
        del user_data["pending_message"]
        data["users"][str(user_id)] = user_data
        self._save_sessions(data)
        
        return {
            "response": "❌ Операция отменена",
            "action": "operation_cancelled"
        }

# Создаем глобальный экземпляр процессора
_processor = SuperEmpathProcessor()

async def tool_lng_telegram_super_empath(
    telegram_context: str,
    prompt_template_name: str = "default_super_empath"
) -> Dict[str, Any]:
    """
    Super Empath - бизнес-логика эмоционального переводчика
    
    Обрабатывает сообщение через эмоциональный переводчик с LLM
    Принимает telegram_context как JSON строку
    """
    
    try:
        if not telegram_context:
            return {"error": "telegram_context is required"}
        
        # Парсим telegram_context из JSON строки
        import json
        try:
            context_obj = json.loads(telegram_context)
            logger.info("Parsed telegram_context from JSON string")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in telegram_context: {e}")
            return {"error": f"Invalid telegram_context JSON: {e}"}
        
        # Проверяем что получили словарь
        if not isinstance(context_obj, dict):
            logger.error(f"telegram_context must be dict, got: {type(context_obj)}")
            return {"error": f"Invalid telegram_context type: {type(context_obj)}"}
        
        # Добавляем prompt_template_name в контекст для использования процессором
        context_obj["prompt_template_name"] = prompt_template_name
        
        # Обрабатываем сообщение
        result = await _processor.handle_command(context_obj)
        
        logger.info(f"Processed message from user {context_obj.get('user_id')}: {context_obj.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in super empath tool: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Super empath processing failed: {e}"}

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Executes the Super Empath tool."""
    try:
        result = await tool_lng_telegram_super_empath(**parameters)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    except Exception as e:
        error_result = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
