from telegram.ext import filters
from database import Database

class DatabaseFilter(filters.MessageFilter):
    def __init__(self, database: Database, name = None, data_filter = False):
        super().__init__(name, data_filter)
        self.database = database

class PendingFilter(DatabaseFilter):
    def filter(self, message):
        usr_id = message.from_user.id
        pending = set(map(int, self.database.data["pending"].keys()))
        return usr_id in pending
    
class MemberFilter(DatabaseFilter):
    def filter(self, message):
        usr_id = message.from_user.id
        members = set(map(int, self.database.data["members"].keys()))
        return usr_id in members