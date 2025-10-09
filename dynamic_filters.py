from telegram import Update
from telegram.ext import filters
from database import Database

class DatabaseFilter(filters.UpdateFilter):
    def __init__(self, database: Database, name = None, data_filter = False):
        super().__init__(name, data_filter)
        self.database = database

class PendingFilter(DatabaseFilter):
    def filter(self, update: Update):
        if update.callback_query:
            usr_id = update.callback_query.from_user.id
        else:
            usr_id = update.message.from_user.id
        pending = set(map(int, self.database.data["pending"].keys()))
        return usr_id in pending
    
class MemberFilter(DatabaseFilter):
    def filter(self, update: Update):
        if update.callback_query:
            usr_id = update.callback_query.from_user.id
        else:
            usr_id = update.message.from_user.id
        members = set(self.database.data["members"].keys())
        return str(usr_id) in members