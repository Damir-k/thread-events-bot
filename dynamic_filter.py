from telegram.ext import filters

class RegisterFilter(filters.MessageFilter):
    def __init__(self, members: set[int], pending: set[int], name = None, data_filter = False):
        super().__init__(name, data_filter)
        self.members = members
        self.pending = pending
    
    def filter(self, message):
        usr_id = message.from_user.id
        return usr_id not in self.members and usr_id not in self.pending
    
    def add_member(self, chat_id : int | str):
        self.members.add(int(chat_id))
    
    def add_pending(self, chat_id : int | str):
        self.pending.add(int(chat_id))

