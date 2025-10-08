from telegram.ext import filters
from database import Database

class RegisterFilter(filters.MessageFilter):
    def __init__(self, database: Database, name = None, data_filter = False):
        super().__init__(name, data_filter)
        self.database = database
    
    def filter(self, message):
        usr_id = message.from_user.id
        members = set(map(int, self.database.data["members"].keys()))
        pending = set(map(int, self.database.data["pending"].keys()))
        return usr_id not in members and usr_id not in pending
    
