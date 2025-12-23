import json
import os
import aiohttp
from typing import Any, Dict

# SciBox LLM API configuration (from environment or defaults)
SCIBOX_API_URL = os.getenv("SCIBOX_API_URL", "https://api.scibox.example.com/v1/generate")
SCIBOX_API_KEY = os.getenv("SCIBOX_API_KEY")
SCIBOX_MODEL = os.getenv("SCIBOX_MODEL", "Qwen2.5-72B-Instruct-AWQ")

async def call_scibox(prompt: str) -> str:
    """
    Вспомогательная функция для вызова LLM-модели через SciBox API с заданным prompt.
    Возвращает сгенерированный моделью текст ответа.
    """
    headers = {"Content-Type": "application/json"}
    if SCIBOX_API_KEY:
        headers["Authorization"] = f"Bearer {SCIBOX_API_KEY}"
    payload = {"model": SCIBOX_MODEL, "prompt": prompt}
    
    timeout = aiohttp.ClientTimeout(total=60.0)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(SCIBOX_API_URL, json=payload, headers=headers) as response:
                response.raise_for_status()
                # Парсим ответ как JSON
                try:
                    data = await response.json()
                except ValueError:
                    raise RuntimeError("SciBox API returned invalid JSON response")
                # Извлекаем текст результата (ключ может называться 'result' или 'text')
                result_text = data.get("result") or data.get("text") or ""
                return result_text
        except aiohttp.ClientError as e:
            raise RuntimeError(f"SciBox API request failed: {e}")

async def analyze_dialog(dialog_text: str) -> Dict[str, Any]:
    """
    Отправляет текст диалога в LLM (через SciBox API) для анализа и парсит результат.
    Возвращает словарь с ключами: goals, skills, experience, challenges, missing_skills.
    """
    # Промпт на русском языке, чтобы модель вернула ответ на русском в требуемом JSON-формате
    prompt = (
        "Проанализируй следующий диалог между карьерным консультантом (ассистентом) и пользователем. "
        "Извлеки из диалога и перечисли:\n"
        "1. Цели пользователя в карьере.\n"
        "2. Его текущие навыки и опыт работы.\n"
        "3. Проблемы или затруднения, с которыми он сталкивается на текущей работе.\n"
        "4. Ключевые навыки или знания, которых ему не хватает для достижения целей.\n\n"
        "Дай ответ в формате JSON с полями: goals, skills, experience, challenges, missing_skills.\n"
        f"Диалог:\n{dialog_text}"
    )
    # Отправляем запрос к LLM-модели через SciBox API и получаем ответ
    result_text = await call_scibox(prompt)
    # Парсим ответ модели как JSON
    try:
        analysis = json.loads(result_text)
    except json.JSONDecodeError as e:
        # Если модель вернула некорректный JSON, возвращаем базовую структуру
        print(f"Warning: Failed to parse LLM response as JSON: {e}")
        analysis = {
            "goals": "Не удалось извлечь цели",
            "skills": "Не удалось извлечь навыки", 
            "experience": "Не удалось извлечь опыт",
            "challenges": "Не удалось извлечь проблемы",
            "missing_skills": []
        }
    return analysis
