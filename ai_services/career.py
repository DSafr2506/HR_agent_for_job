import json
from typing import List, Dict, Optional

from .utils.career_agent import CareerAgent
from config.config import AI_API_KEY

class AICareerService:
    def __init__(self, api_key, max_history_length: int = 10):
        """
        Инициализация сервиса чата с ИИ-агентом
        
        Args:
            api_key: ключ для работы модели
            max_history_length: максимальное количество сообщений в истории диалога
        """
        self.dialog_history: Dict[str, List[Dict]] = {}
        self.max_history_length = max_history_length
        self.career_agent = CareerAgent(api_key=api_key)
    
    async def process_message(self, user_id: str, message: str) -> str:
        """
        Обработка сообщения пользователя и получение ответа от ИИ-агента
        
        Args:
            user_id: идентификатор пользователя
            message: сообщение пользователя
            
        Returns:
            Ответ ИИ-агента в виде текста
        """
        self._add_to_history(user_id, "user", message)
        
        history_json = self._get_history_json(user_id)
        
        ai_response = await self._call_ai_agent(history_json)
        
        self._add_to_history(user_id, "assistant", ai_response)
        
        return ai_response
    
    def _add_to_history(self, user_id: str, role: str, content: str):
        """
        Добавление сообщения в историю диалога
        
        Args:
            user_id: идентификатор пользователя
            role: роль отправителя (user/assistant)
            content: содержание сообщения
        """
        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        
        self.dialog_history[user_id].append({
            "role": role,
            "content": content
        })
        
        if len(self.dialog_history[user_id]) > self.max_history_length:
            self.dialog_history[user_id] = self.dialog_history[user_id][-self.max_history_length:]
    
    def _get_history_json(self, user_id: str) -> str:
        """
        Получение истории диалога в формате JSON
        
        Args:
            user_id: идентификатор пользователя
            
        Returns:
            История диалога в формате JSON
        """
        history = self.dialog_history.get(user_id, [])
        return json.dumps(history, ensure_ascii=False, indent=2)
    
    async def _call_ai_agent(self, history_json: str) -> str:
        """
        Вызов ИИ-агента с историей диалога
        
        Args:
            history_json: история диалога в формате JSON
            
        Returns:
            Ответ ИИ-агента
        """
        return await self.career_agent.get_response(history_json)
    
    def get_history(self, user_id: str) -> List[Dict]:
        """
        Получение истории диалога для пользователя
        
        Args:
            user_id: идентификатор пользователя
            
        Returns:
            История диалога в виде списка сообщений
        """
        return self.dialog_history.get(user_id, [])
    
    def clear_history(self, user_id: str):
        """
        Очистка истории диалога для пользователя
        
        Args:
            user_id: идентификатор пользователя
        """
        if user_id in self.dialog_history:
            del self.dialog_history[user_id] 

ai_service = AICareerService(api_key = AI_API_KEY)