# Основные классы и функции
from .ai_services.utils.career_agent import CareerAgent
from .ai_services.utils.unified_interface import CareerAdvisorInterface
from .ai_services.utils.prepare_profile import get_text_profile

# Функции для быстрого доступа
from .ai_services.utils.unified_interface import (
    quick_analyze_conversation,
    quick_get_profile,
    quick_find_resources,
    quick_analyze_messages
)

# Обратная совместимость с оригинальным async-агентом
from .career_advisor_agent_async.main import run_agent_async
from .career_advisor_agent_async.loader import load_conversation, format_conversation
from .career_advisor_agent_async.analyzer import analyze_dialog
from .career_advisor_agent_async.searcher import find_resources_for_skill
from .career_advisor_agent_async.recommender import generate_final_message

__all__ = [
    # Основные классы
    'CareerAgent',
    'CareerAdvisorInterface',
    
    # Утилиты
    'get_text_profile',
    
    # Функции быстрого доступа
    'quick_analyze_conversation',
    'quick_get_profile',
    'quick_find_resources',
    'quick_analyze_messages',
    
    # Обратная совместимость
    'run_agent_async',
    'load_conversation', 
    'format_conversation',
    'analyze_dialog',
    'find_resources_for_skill',
    'generate_final_message'
]
