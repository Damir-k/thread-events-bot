from telegram.ext import CallbackContext, ExtBot
from database import Database
from dotenv import dotenv_values


class CustomContext(CallbackContext[ExtBot, dict, None, dict]):
    """Custom class for context."""

    def __init__(self, application, chat_id = None, user_id = None):
        super().__init__(application, chat_id, user_id)
        self.config = dotenv_values(".env")
        self.database = Database("thread_members.json")
