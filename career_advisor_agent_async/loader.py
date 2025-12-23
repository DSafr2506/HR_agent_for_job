import json
import asyncio
from typing import List, Dict

async def load_conversation(json_path: str) -> List[Dict]:
    """
    Загружает историю диалога из JSON-файла и возвращает список сообщений.
    Каждый элемент списка – словарь с ключами 'role' и 'message'.
    """
    # Читаем JSON-файл асинхронно (в отдельном потоке, чтобы не блокировать цикл событий)
    def _load_file(path: str) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    data = await asyncio.to_thread(_load_file, json_path)
    # Валидация структуры данных
    if not isinstance(data, list):
        raise ValueError("JSON file format is invalid: expected a list of messages")
    for msg in data:
        if 'role' not in msg or 'message' not in msg:
            raise ValueError("JSON messages must contain 'role' and 'message' fields")
    return data

def format_conversation(messages: List[Dict]) -> str:
    """
    Преобразует список сообщений в единый текстовый диалог для анализа LLM.
    Возвращает строку, объединяющую все сообщения с указанием роли.
    """
    formatted_lines = []
    for msg in messages:
        role = msg['role'].lower()
        content = msg['message']
        # Обозначаем роли явно в тексте диалога
        if role == 'user':
            formatted_lines.append(f"Пользователь: {content}")
        elif role in ('assistant', 'ai'):
            formatted_lines.append(f"Консультант: {content}")
        else:
            formatted_lines.append(f"{role.capitalize()}: {content}")
    # Объединяем список строк диалога в один текст
    return "\n".join(formatted_lines)
