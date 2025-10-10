# Телеграм бот для мероприятий ПО "Нить"
Чтобы запустить его, вам необходимо 

1) склонировать репозиторий
2) выполнить `pip install -r requirements.txt`
3) создать файл `.env` с данным содержимым:
```
TOKEN="bot token"
ADMIN_CHAT_ID="admin chat id"
OWNER_CHAT_ID="owner chat id"
EVENTS_CHAT_ID="events chat id"
ERROR_CHAT_ID="error chat id"
```
4) запустить `python bot.py`

Владельцу доступны команды `/list_all_events`, `/admin`, `/restart`
