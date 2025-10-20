from telegram.ext import CallbackContext, ExtBot

from dotenv import dotenv_values
from enum import Enum
from datetime import date
import logging

from database import Database

class State(Enum):
    EVENT_NAME = 1
    LOCATION = 2
    DATE_TIME = 3
    DESCRIPTION = 4
    CONFIRM_EVENT = 5
    EXPIRATION_DATE = 6
    EVENT_AGE = 7
    EVENT_SIZE = 8

class ExactMessages(Enum):
    MAIN_MENU = "Вернуться в главное меню"

class CustomContext(CallbackContext[ExtBot, dict, None, dict]):
    """Custom class for context."""
    def __init__(self, application, chat_id = None, user_id = None):
        super().__init__(application, chat_id, user_id)
        self.config = dotenv_values(".env")
        application.bot_data["ERROR_CHAT_ID"] = self.config["ERROR_CHAT_ID"]
        self.database = Database("thread_members.json")
        self.logger = logging.getLogger()

    def get_user_status(self, chat_id) -> str:
        if str(chat_id) in self.database.data["members"]:
            return "Ниточка 🧵"
        if str(chat_id) in self.database.data["pending"]:
            return "На рассмотрении 🕞"
        return "Неизвестный ❓ \n - Подайте заявку через /register"

    def event_accessible(self, event_id: int | str, chat_id: int | str) -> bool:
        event = self.database.data["events"][str(event_id)]
        expired = date.fromisoformat(event["expiration_date"]) < date.today()
        if expired and event["status"] != "expired":
            self.database.data["events"][str(event_id)]["status"] = "expired"
            self.database.save()
        is_author = event["author"] == int(chat_id)
        is_active = event["status"] == "active" or event["status"] == "cool"
        return (is_author) or (is_active and not expired)

    def get_events(self, chat_id, filter_available=True) -> dict[str, dict]:
        events = self.database.data["events"]
        if not filter_available:
            return events
        accessible_events = filter(
            lambda x: self.event_accessible(x[0], chat_id), 
            events.items()
        )
        return dict(accessible_events)
    
    @staticmethod
    def get_badge(events: int) -> str:
        return "🙆"