import json


class Database:
    def __init__(self, filename: str):
        with open(filename, "r") as file:
            self.data: dict[int, dict] = json.load(file)
        self.filename = filename
        if "members" not in self.data:
            self.data["members"] = dict()
        if "pending" not in self.data:
            self.data["pending"] = dict()
        if "events" not in self.data:
            self.data["events"] = dict()
        if "_last_event_id" not in self.data:
            self.data["_last_event_id"] = 1

    def save(self):
        with open(self.filename, "w") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def save_entry(self, entry_type: str, chat_id: int | str, username: str, name: str):
        self.data[entry_type][str(chat_id)] = {
            "username": "@" + username,
            "name": name,
            "events": []
        }
        self.save()

    def delete_entry(self, entry_type: str, chat_id: int | str):
        self.data[entry_type].pop(str(chat_id))
        self.save()
    
    def save_id(self, username, chat_id):
        self.data["ids"][username] = chat_id
        self.save()
    
    def next_event_id(self) -> int:
        self.data["_last_event_id"] += 1
        self.save()
        return self.data["_last_event_id"]