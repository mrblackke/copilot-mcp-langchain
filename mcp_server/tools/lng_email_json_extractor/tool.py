import os
import json
from typing import List, Dict, Any, Optional
import mcp.types as types

# Для LLM/промта (заглушка, можно интегрировать с MCP LLM tool)
def apply_prompt_to_email(email: Dict[str, Any], prompt: str) -> Optional[Dict[str, Any]]:
    """
    Применяет промт к письму. Здесь можно интегрировать LLM или парсить ключевые слова.
    Возвращает структурированные данные по заказу, если письмо подходит, иначе None.
    """
    # Пример: если в теме есть слово "заказ" — вернуть часть информации
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


def extract_info_from_json(json_dir: str, prompt: str) -> List[Dict[str, Any]]:
    """
    Читает все JSON-файлы с письмами и применяет фильтрацию по промту.
    """
    results = []
    for fname in os.listdir(json_dir):
        if fname.endswith('.json'):
            fpath = os.path.join(json_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for email in data.get('emails', []):
                        info = apply_prompt_to_email(email, prompt)
                        if info:
                            info['source_file'] = fname
                            results.append(info)
            except Exception as e:
                print(f"Ошибка чтения {fname}: {e}")
    return results


def tool_lng_email_json_extractor(prompt: str, json_dir: str = None) -> str:
    """
    MCP tool: фильтрация и выгрузка информации из email JSON по промту.
    """
    if not json_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        json_dir = os.path.join(base_dir, 'extracted_emails')
    if not os.path.exists(json_dir):
        return f"❌ Папка {json_dir} не найдена."
    results = extract_info_from_json(json_dir, prompt)
    if not results:
        return f"❌ Не найдено писем по промту: {prompt}"
    msg = f"✅ Найдено {len(results)} писем по промту '{prompt}':\n"
    for i, info in enumerate(results[:10], 1):
        msg += f"{i}. {info['date']} | {info['from']} | {info['subject']} | {info['source_file']}\n"
    if len(results) > 10:
        msg += f"... и ещё {len(results)-10} писем\n"
    return msg

# MCP required functions
tool_info = lambda: {
    "description": "Фильтрует и выгружает информацию из email JSON-файлов по промту (ключевое слово или LLM-промт)",
    "schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Ключевое слово или промт для фильтрации писем"},
            "json_dir": {"type": "string", "description": "Папка с JSON-файлами (по умолчанию extracted_emails)"}
        },
        "required": ["prompt"]
    }
}

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    prompt = parameters.get("prompt")
    json_dir = parameters.get("json_dir")
    result = tool_lng_email_json_extractor(prompt, json_dir)
    return [types.TextContent(type="text", text=result)]

if __name__ == "__main__":
    prompt = input("Введите промт/ключевое слово: ")
    print(tool_lng_email_json_extractor(prompt))
