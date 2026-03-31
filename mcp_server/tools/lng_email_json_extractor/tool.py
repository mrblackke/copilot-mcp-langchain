import os
import json
from typing import List, Dict, Any, Optional
import mcp.types as types
from mcp_server.llm import llm
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate

async def apply_llm_to_email(email: Dict[str, Any], prompt: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    Применяет LLM для извлечения структурированной информации из письма.
    Возвращает структурированные данные по заказу, если LLM смог извлечь информацию, иначе None.
    
    Args:
        email: Словарь с данными письма
        prompt: Промт для анализа
        timeout: Таймаут в секундах для запроса к LLM
    """
    import asyncio
    from langchain.output_parsers import OutputFixingParser
    
    model = llm()
    
    # Определяем схему для структурированного вывода
    response_schemas = [
        ResponseSchema(name="relevant", description="true если письмо содержит информацию по запросу, false если нет"),
        ResponseSchema(name="order_id", description="Номер заказа, если есть"),
        ResponseSchema(name="store_name", description="Название магазина или сервиса"),
        ResponseSchema(name="order_date", description="Дата заказа"),
        ResponseSchema(name="order_total", description="Общая сумма заказа"),
        ResponseSchema(name="currency", description="Валюта заказа"),
        ResponseSchema(name="delivery_status", description="Статус доставки"),
        ResponseSchema(name="products", description="Список продуктов в заказе, если доступно")
    ]
    
    parser = StructuredOutputParser.from_response_schemas(response_schemas)
    # Добавляем парсер с исправлением ошибок для более надежного парсинга
    fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=model)
    format_instructions = parser.get_format_instructions()
    
    template = """
    Ты опытный аналитик, который извлекает информацию о заказах из электронных писем.
    Проанализируй это письмо и определи, содержит ли оно информацию, соответствующую запросу: {prompt}.
    
    ПИСЬМО:
    Отправитель: {from_email}
    Тема: {subject}
    Дата: {date}
    
    Содержимое:
    {body}
    
    {format_instructions}
    """
    
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["prompt", "from_email", "subject", "date", "body"],
        partial_variables={"format_instructions": format_instructions}
    )
    
    chain = prompt_template | model | fixing_parser
    
    try:
        # Добавляем обработку таймаута
        result = await asyncio.wait_for(
            chain.ainvoke({
                "prompt": prompt,
                "from_email": email.get('from', ''),
                "subject": email.get('subject', ''),
                "date": email.get('date', ''),
                "body": email.get('body', '')[:2000]  # Уменьшаем размер для ускорения обработки
            }),
            timeout=timeout
        )
        
        print(f"LLM результат для письма {email.get('id')}: {result.get('relevant')}")
        
        # Если LLM определил, что письмо релевантное
        if result.get("relevant") == "true":
            # Добавляем исходную информацию о письме
            email_info = {
                'id': email.get('id'),
                'subject': email.get('subject'),
                'from': email.get('from'),
                'date': email.get('date'),
                'body': email.get('body')[:200],  # preview
                'mailbox': email.get('mailbox'),
                'extracted_at': email.get('extracted_at'),
                # Добавляем извлеченную LLM информацию
                'llm_extracted_data': {
                    'order_id': result.get('order_id'),
                    'store_name': result.get('store_name'),
                    'order_date': result.get('order_date'),
                    'order_total': result.get('order_total'),
                    'currency': result.get('currency'),
                    'delivery_status': result.get('delivery_status'),
                    'products': result.get('products')
                }
            }
            return email_info
    except asyncio.TimeoutError:
        print(f"Таймаут при обработке письма {email.get('id')} с промтом: {prompt}")
    except Exception as e:
        print(f"Ошибка при обработке LLM для письма {email.get('id')}: {e}")
    
    return None

# Базовая функция для фильтрации по ключевым словам
def apply_prompt_to_email(email: Dict[str, Any], prompt: str) -> Optional[Dict[str, Any]]:
    """
    Применяет промт к письму для поиска по ключевым словам.
    Возвращает базовые данные о письме, если оно подходит по ключевым словам, иначе None.
    """
    # Если в теме или теле письма есть ключевое слово
    if prompt.lower() in email.get('subject', '').lower() or prompt.lower() in email.get('body', '').lower():
        return {
            'id': email.get('id'),
            'subject': email.get('subject'),
            'from': email.get('from'),
            'date': email.get('date'),
            'body': email.get('body')[:200],  # preview
            'mailbox': email.get('mailbox'),
            'extracted_at': email.get('extracted_at')
        }
    return None


async def extract_info_from_json(json_dir: str, prompt: str, use_llm: bool = False, llm_timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Читает все JSON-файлы с письмами и применяет фильтрацию по промту.
    Если use_llm=True, использует LLM для извлечения структурированных данных из писем.
    
    Args:
        json_dir: Директория с JSON файлами писем
        prompt: Ключевое слово или промт для фильтрации
        use_llm: Использовать ли LLM для анализа
        llm_timeout: Таймаут в секундах для запросов к LLM
    """
    results = []
    for fname in os.listdir(json_dir):
        if fname.endswith('.json'):
            fpath = os.path.join(json_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Проверяем структуру JSON (может быть вложенной)
                    emails_list = []
                    if isinstance(data, dict) and 'emails' in data:
                        if isinstance(data['emails'], dict) and 'emails' in data['emails']:
                            # Вложенная структура: data['emails']['emails'] - список писем
                            emails_list = data['emails']['emails']
                        elif isinstance(data['emails'], list):
                            # Простая структура: data['emails'] - список писем
                            emails_list = data['emails']
                    
                    for email in emails_list:
                        # Сначала применяем базовую фильтрацию по ключевым словам
                        info = apply_prompt_to_email(email, prompt)
                        
                        if info:
                            # Если письмо подходит по ключевым словам и нужен анализ через LLM
                            if use_llm:
                                llm_info = await apply_llm_to_email(email, prompt, llm_timeout)
                                if llm_info:
                                    llm_info['source_file'] = fname
                                    results.append(llm_info)
                                    continue
                            
                            # Если не использовался LLM или LLM не вернул результат
                            info['source_file'] = fname
                            results.append(info)
            except Exception as e:
                print(f"Ошибка чтения {fname}: {e}")
    return results


async def tool_lng_email_json_extractor(prompt: str, json_dir: str = None, output_file: str = None, save_output: bool = False, use_llm: bool = False, llm_timeout: int = 30) -> str:
    """
    MCP tool: фильтрация и выгрузка информации из email JSON по промту.
    
    Args:
        prompt: Ключевое слово или промт для фильтрации писем
        json_dir: Папка с JSON-файлами (по умолчанию extracted_emails)
        output_file: Имя файла для сохранения результатов (без расширения)
        save_output: Сохранять ли результаты в файл
        use_llm: Использовать LLM для извлечения структурированных данных (по умолчанию False)
        llm_timeout: Таймаут в секундах для запросов к LLM (по умолчанию 30)
    
    Returns:
        Сообщение о результатах выполнения
    """
    if not json_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        json_dir = os.path.join(base_dir, 'extracted_emails')
    if not os.path.exists(json_dir):
        return f"❌ Папка {json_dir} не найдена."
    
    print(f"Начинаем обработку писем по запросу '{prompt}' в директории {json_dir}")
    if use_llm:
        print(f"Используем LLM для анализа с таймаутом {llm_timeout} секунд")
    
    results = await extract_info_from_json(json_dir, prompt, use_llm, llm_timeout)
    if not results:
        return f"❌ Не найдено писем по промту: {prompt}"
    
    mode = "с использованием LLM" if use_llm else "по ключевому слову"
    msg = f"✅ Найдено {len(results)} писем по промту '{prompt}' {mode}:\n"
    
    for i, info in enumerate(results[:10], 1):
        msg += f"{i}. {info['date']} | {info['from']} | {info['subject']} | {info['source_file']}"
        if use_llm and 'llm_extracted_data' in info:
            llm_data = info['llm_extracted_data']
            if llm_data.get('order_id'):
                msg += f" | Заказ: {llm_data.get('order_id')}"
            if llm_data.get('order_total') and llm_data.get('currency'):
                msg += f" | Сумма: {llm_data.get('order_total')} {llm_data.get('currency')}"
        msg += "\n"
    
    if len(results) > 10:
        msg += f"... и ещё {len(results)-10} писем\n"
    
    # Сохранение результатов в файл, если указано
    if save_output or output_file:
        if not output_file:
            # Создаем имя файла на основе текущей даты и промта
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"email_extract_{prompt.replace(' ', '_')}_{timestamp}"
        
        # Путь для сохранения результатов
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_dir = os.path.join(base_dir, 'extracted_data')
        os.makedirs(output_dir, exist_ok=True)
        
        # Сохраняем в JSON
        json_path = os.path.join(output_dir, f"{output_file}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"results": results, "query": prompt, "total_found": len(results)}, f, 
                      ensure_ascii=False, indent=2)
        
        msg += f"\nРезультаты сохранены в файл: {json_path}"
    
    return msg

# MCP required functions
async def tool_info() -> dict:
    return {
        "description": "Фильтрует и выгружает информацию из email JSON-файлов по промту (ключевое слово или LLM-промт)",
        "schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Ключевое слово или промт для фильтрации писем"},
                "json_dir": {"type": "string", "description": "Папка с JSON-файлами (по умолчанию extracted_emails)"},
                "output_file": {"type": "string", "description": "Имя файла для сохранения результатов (без расширения)"},
                "save_output": {"type": "boolean", "description": "Сохранять ли результаты в файл (по умолчанию false)"},
                "use_llm": {"type": "boolean", "description": "Использовать LLM для извлечения структурированных данных (по умолчанию false)"},
                "llm_timeout": {"type": "integer", "description": "Таймаут в секундах для запросов к LLM (по умолчанию 30)"}
            },
            "required": ["prompt"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    prompt = parameters.get("prompt")
    json_dir = parameters.get("json_dir")
    output_file = parameters.get("output_file")
    save_output = parameters.get("save_output", False)
    use_llm = parameters.get("use_llm", False)
    llm_timeout = parameters.get("llm_timeout", 30)
    result = await tool_lng_email_json_extractor(prompt, json_dir, output_file, save_output, use_llm, llm_timeout)
    return [types.TextContent(type="text", text=result)]

if __name__ == "__main__":
    import asyncio
    prompt = input("Введите промт/ключевое слово: ")
    use_llm = input("Использовать LLM для анализа? (y/n): ").lower() == 'y'
    
    llm_timeout = 30
    if use_llm:
        try:
            timeout_input = input(f"Таймаут для LLM в секундах (по умолчанию {llm_timeout}): ")
            if timeout_input.strip():
                llm_timeout = int(timeout_input)
        except ValueError:
            print(f"Неверный формат таймаута, будет использовано значение по умолчанию: {llm_timeout} сек.")
    
    save_output = input("Сохранить результаты в файл? (y/n): ").lower() == 'y'
    output_file = None
    if save_output:
        output_file = input("Имя файла (оставьте пустым для автоматического имени): ") or None
    
    # Устанавливаем меньший таймаут для тестирования
    if use_llm and not llm_timeout:
        llm_timeout = 20
    
    print(f"Запуск инструмента с параметрами: prompt='{prompt}', use_llm={use_llm}, llm_timeout={llm_timeout}, save_output={save_output}")
    result = asyncio.run(tool_lng_email_json_extractor(prompt, None, output_file, save_output, use_llm, llm_timeout))
    print(result)
