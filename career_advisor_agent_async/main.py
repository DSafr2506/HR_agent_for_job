import asyncio
import aiohttp
from . import loader, analyzer, searcher, recommender

async def run_agent_async(json_path: str) -> str:
    """
    Запускает пайплайн карьерного агента по диалогу из указанного JSON-файла.
    Последовательно выполняет анализ диалога, поиск ресурсов и генерацию рекомендаций.
    Возвращает финальное рекомендационное сообщение (строка).
    """
    # 1. Загрузка диалога и форматирование в текст
    messages = await loader.load_conversation(json_path)
    dialog_text = loader.format_conversation(messages)
    # 2. Анализ диалога с помощью LLM для извлечения профиля пользователя
    profile = await analyzer.analyze_dialog(dialog_text)
    if not profile or "missing_skills" not in profile:
        raise ValueError("Analyzer failed to extract profile or missing skills")
    missing_skills = profile["missing_skills"]
    # 3. Асинхронный поиск ресурсов по недостающим навыкам
    resources_by_skill = {}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        tasks = [searcher.find_resources_for_skill(skill, session) for skill in missing_skills]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for skill, result in zip(missing_skills, results):
            if isinstance(result, Exception):
                # Если поиск по навыку завершился с ошибкой, используем пустой список ресурсов для него
                resources_by_skill[skill] = {"courses": [], "articles": [], "vacancies": [], "projects": [], "competitions": []}
            else:
                resources_by_skill[skill] = result
    # 4. Объединение результатов по всем навыкам в единые списки по категориям
    combined_recommendations = {"courses": [], "articles": [], "vacancies": [], "projects": [], "competitions": []}
    for skill, res in resources_by_skill.items():
        for course in res.get("courses", []):
            course["skill"] = skill
            combined_recommendations["courses"].append(course)
        for article in res.get("articles", []):
            article["skill"] = skill
            combined_recommendations["articles"].append(article)
        for vac in res.get("vacancies", []):
            vac["skill"] = skill
            combined_recommendations["vacancies"].append(vac)
        for proj in res.get("projects", []):
            proj["skill"] = skill
            combined_recommendations["projects"].append(proj)
        for comp in res.get("competitions", []):
            comp["skill"] = skill
            combined_recommendations["competitions"].append(comp)
    # 5. Генерация итогового сообщения с рекомендациями с помощью LLM
    final_message = await recommender.generate_final_message(profile, combined_recommendations)
    return final_message

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m career_advisor_agent_async <path/to/conversation.json>")
    else:
        result_msg = asyncio.run(run_agent_async(sys.argv[1]))
        print(result_msg)
