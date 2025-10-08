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

    def save_entry(self, entry_type: str, chat_id: int | str, username: str, name: str):
        self.data[entry_type][str(chat_id)] = {
            "username": "@" + username,
            "name": name,
        }
        with open(self.filename, "w") as file:
            json.dump(self.data, file)

    def delete_entry(self, entry_type: str, chat_id: int | str):
        self.data[entry_type].pop(str(chat_id))
        with open(self.filename, "w") as file:
            json.dump(self.data, file)