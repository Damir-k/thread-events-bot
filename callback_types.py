
class RegisterVerdict:
    def __init__(self, user_id: int, accept: bool):
        self.user_id = user_id
        self.accept = accept

class EventVerdict:
    def __init__(self, event_id, accept: bool):
        self.event_id = event_id
        self.accept = accept

class ManageEvent:
    def __init__(self, event_id):
        self.event_id = event_id