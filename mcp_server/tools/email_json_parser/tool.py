import os
import json
from typing import List, Dict, Any, Optional
import mcp.types as types
import asyncio

# Формирует LLM-промт для письма по вашему шаблону
def build_llm_prompt(email: Dict[str, Any], user_prompt: str) -> str:
    return f"""
{user_prompt}\n\n### Email Metadata:\n- From: {email.get('from', 'unknown')}\n- Subject: {email.get('subject', 'unknown')}\n- Date: {email.get('date', 'unknown')}\n\n### Email Body:\n{email.get('body', '')}\n\n### Response Format (JSON only):\n"""

# Асинхронный вызов LLM напрямую
async def call_llm(prompt: str) -> Optional[dict]:
    try:
        import re
        import json as pyjson
        from mcp_server.llm import llm
        model = llm()
        response = await model.ainvoke(prompt)
        text = response.content if hasattr(response, 'content') else str(response)
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return pyjson.loads(match.group(0))
    except Exception as e:
        print(f"Ошибка LLM: {e}")
    return None

# Основная функция: перебирает письма, вызывает LLM, собирает результаты
async def extract_orders_from_json(json_dir: str, user_prompt: str) -> List[Dict[str, Any]]:
    results = []
    for fname in os.listdir(json_dir):
        if fname.endswith('.json'):
            fpath = os.path.join(json_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    emails_data = data.get('emails', [])
                    if isinstance(emails_data, dict) and 'emails' in emails_data:
                        emails_list = emails_data['emails']
                    elif isinstance(emails_data, list):
                        emails_list = emails_data
                    else:
                        emails_list = []
                    for email in emails_list:
                        prompt = build_llm_prompt(email, user_prompt)
                        llm_result = await call_llm(prompt)
                        if llm_result:
                            llm_result['source_file'] = fname
                            llm_result['email_id'] = email.get('id')
                            results.append(llm_result)
            except Exception as e:
                print(f"Ошибка чтения {fname}: {e}")
    return results

DEFAULT_PROMPT = (
    "You are a structured data parser. Your task is to extract supplier order information from email content and metadata.\n\n"
    "Extract the following fields. If any field is missing, use the value 'unknown'.\n\n"
    "- supplier_name: Look in the sender's email, subject line, or company name in the email body.\n"
    "- order_date: Use the date in the body if available; otherwise, use the email metadata date.\n"
    "- order_number: Look for a specific number in the subject, sender, or body.\n"
    "- items: A list of ordered items. Each item must be a JSON object with name, quantity, unit, and price.\n\n"
    "### Email Metadata:\n"
    "- From: {{ $json.emailSender }}\n"
    "- Subject: {{ $json.emailSubject }}\n"
    "- Date: {{ $json.emailDate }}\n\n"
    "### Email Body:\n"
    "{{ $json.emailBody }}\n\n"
    "### Response Format (JSON only):\n"
    "{\n"
    "  \"supplier_name\": \"Example LLC\",\n"
    "  \"order_date\": \"YYYY-MM-DD\",\n"
    "  \"order_number\": \"123456\",\n"
    "  \"items\": [\n"
    "    {\n"
    "      \"name\": \"Item Name\",\n"
    "      \"quantity\": 1,\n"
    "      \"unit\": \"pcs\",\n"
    "      \"price\": 100.0\n"
    "    }\n"
    "  ]\n"
    "}\n"
)

async def tool_email_json_parser(prompt: str = None, json_dir: str = None) -> str:
    """
    MCP tool: фильтрация и выгрузка информации из email JSON по промту (LLM).
    """
    if prompt is None:
        prompt = DEFAULT_PROMPT
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if not json_dir:
        json_dir = os.path.join(base_dir, 'extracted_emails')
    if not os.path.exists(json_dir):
        return f"❌ Папка {json_dir} не найдена."
    results = await extract_orders_from_json(json_dir, prompt)
    if not results:
        return f"❌ Не найдено заказов по промту: {prompt}"
    # Сохраняем структурированные данные в папку parsed_orders
    import datetime
    parsed_dir = os.path.join(base_dir, 'parsed_orders')
    os.makedirs(parsed_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_path = os.path.join(parsed_dir, f'orders_{timestamp}.json')
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ Ошибка при сохранении файла: {e}"
    return f"✅ Заказы ({len(results)}) сохранены в {output_path}"

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
    result = await tool_email_json_parser(prompt, json_dir)
    return [types.TextContent(type="text", text=result)]

if __name__ == "__main__":
    prompt = input("Введите промт/ключевое слово: ")
    print(asyncio.run(tool_email_json_parser(prompt)))
