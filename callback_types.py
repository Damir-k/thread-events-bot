
class RegisterVerdict:
    def __init__(self, user_id: int, accept: bool):
        self.user_id = user_id
        self.accept = accept

class EventVerdict:
    def __init__(self, event_id, accept: bool):
        self.event_id = event_id
        self.accept = accept

class ShowEvent:
    def __init__(self, event_id):
        self.event_id = event_id

class ManageEvent:
    def __init__(self, action, event_id):
        self.action = action
        self.event_id = event_id

class EditEvent:
    def __init__(self, mode, event_id, chat_id=None, message_id=None):
        self.mode = mode
        self.event_id = event_id
        self.chat_id = chat_id
        self.message_id = message_id