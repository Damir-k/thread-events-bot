from telegram.ext import CallbackContext, ExtBot
from database import Database
from dotenv import dotenv_values


class CustomContext(CallbackContext[ExtBot, dict, None, dict]):
    """Custom class for context."""
    def __init__(self, application, chat_id = None, user_id = None):
        super().__init__(application, chat_id, user_id)
        self.config = dotenv_values(".env")
        self.database = Database("thread_members.json")

    def get_user_status(self, chat_id) -> str:
        if str(chat_id) in self.database.data["members"]:
            return "Ниточка 🧵"
        if str(chat_id) in self.database.data["pending"]:
            return "На рассмотрении 🕞"
        return "Неизвестный ❓ \n - Подайте заявку через /register"

    def get_events(self, chat_id) -> list[str]:
        return []
    
    @staticmethod
    def get_badge(events: int) -> str:
        return "🙆"