from typing import Dict, List
from .analyzer import call_scibox

def format_recommendations(user_profile: dict, recommendations: Dict[str, List[Dict]]) -> str:
    """
    Формирует финальный промпт для LLM на основе профиля пользователя и собранных рекомендаций.
    Возвращает строку с перечислением всех рекомендаций, структурированных по категориям.
    """
    goals = user_profile.get("goals", "")
    challenges = user_profile.get("challenges", "")
    missing_skills = user_profile.get("missing_skills", [])
    intro = (f"Пользователь стремится: {goals}.\n"
             f"Текущие трудности: {challenges}.\n"
             f"Выявленные пробелы в навыках: {', '.join(missing_skills)}.\n\n")
    intro += "На основании этого, сгенерируй персональные рекомендации для пользователя. " \
             "Представь их структурировано по категориям (курсы, статьи, вакансии, проекты, соревнования) " \
             "и поясни, как каждый пункт поможет закрыть пробелы и достичь целей.\n\n"
    # Добавляем список ресурсов в текст промпта, чтобы модель видела ссылки и названия
    prompt_lines = [intro, "Ресурсы для рекомендаций:\n"]
    if recommendations.get("courses"):
        prompt_lines.append("Курсы:\n")
        for c in recommendations["courses"]:
            prompt_lines.append(f"- {c['title']} ({c['url']})")
    if recommendations.get("articles"):
        prompt_lines.append("\nСтатьи:\n")
        for a in recommendations["articles"]:
            prompt_lines.append(f"- {a['title']} ({a['url']})")
    if recommendations.get("vacancies"):
        prompt_lines.append("\nВакансии:\n")
        for v in recommendations["vacancies"]:
            prompt_lines.append(f"- {v['title']} ({v['url']})")
    if recommendations.get("projects"):
        prompt_lines.append("\nOpen-source проекты:\n")
        for p in recommendations["projects"]:
            title = p['title']; url = p['url']
            prompt_lines.append(f"- {title} ({url})")
    if recommendations.get("competitions"):
        prompt_lines.append("\nСоревнования:\n")
        for comp in recommendations["competitions"]:
            prompt_lines.append(f"- {comp['title']} ({comp['url']})")
    prompt_lines.append("\nТеперь составь итоговое сообщение для пользователя:")
    return "\n".join(prompt_lines)

async def generate_final_message(user_profile: dict, all_recommendations: Dict[str, List[Dict]]) -> str:
    """
    Генерирует финальный текст рекомендаций для пользователя, обращаясь к LLM (через SciBox API).
    """
    try:
        # Формируем промпт для модели на основе профиля и списка ресурсов
        prompt = format_recommendations(user_profile, all_recommendations)
        # Отправляем промпт в LLM через SciBox API и получаем финальное сообщение
        result_text = await call_scibox(prompt)
        return result_text
    except Exception as e:
        # В случае ошибки возвращаем базовое сообщение с рекомендациями
        print(f"Warning: Failed to generate final message via LLM: {e}")
        return format_fallback_recommendations(user_profile, all_recommendations)

def format_fallback_recommendations(user_profile: dict, all_recommendations: Dict[str, List[Dict]]) -> str:
    """
    Формирует базовое сообщение с рекомендациями без использования LLM.
    """
    goals = user_profile.get("goals", "развитие карьеры")
    missing_skills = user_profile.get("missing_skills", [])
    
    message = f"Основываясь на ваших целях ({goals}) и выявленных пробелах в навыках ({', '.join(missing_skills)}), "
    message += "рекомендую следующие ресурсы:\n\n"
    
    for category, items in all_recommendations.items():
        if items:
            category_names = {
                "courses": "Курсы",
                "articles": "Статьи", 
                "vacancies": "Вакансии",
                "projects": "Проекты",
                "competitions": "Соревнования"
            }
            message += f"{category_names.get(category, category)}:\n"
            for item in items[:3]:  # Показываем только топ-3
                message += f"- {item['title']}: {item['url']}\n"
            message += "\n"
    
    return message
