from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, filters

from datetime import date
import re

from custom_context import CustomContext, State
from dynamic_filters import MemberFilter
from callback_types import EventVerdict, ManageEvent

def get_readable_status(status: str) -> str:
    match status:
        case "pending":
            readable_status = "На рассмотрении 👀"
        case "expired":
            readable_status = "Просрочено ⌛"
        case "declined":
            readable_status = "Отклонено ❌"
        case "active":
            readable_status = "Активно 🟢"
        case "inactive":
            readable_status = "Скрыто 😶‍🌫️"
        case _:
            readable_status = "??? Поздравляю вы сломали бота, напишите @damirablv"
    return readable_status

async def new_event(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(None)
    if (~MemberFilter(context.database)).check_update(update):
        await update.effective_message.reply_text("Зарегистрируйтесь через /register, чтобы создать мероприятие")
        return ConversationHandler.END

    await update.effective_user.send_message("Ура! Введите короткое название нового мероприятия:")
    return State.EVENT_NAME

async def get_event_name(update: Update, context: CustomContext):
    context.user_data['event_name'] = update.message.text_html
    await update.message.reply_text("Супер, где оно происходит? (Адрес/расположение)")
    return State.LOCATION

async def get_event_location(update: Update, context: CustomContext):
    context.user_data['location'] = update.message.text_html
    await update.message.reply_text("Когда планируется? (Дата/время в свободном формате)")
    return State.DATE_TIME

async def get_event_datetime(update: Update, context: CustomContext):
    context.user_data['datetime'] = update.message.text_html
    await update.message.reply_text("\n".join([
        "Введите дату, после которой событие уже не актульно.",
        "(Скорее всего это через 1 день после мероприятия)",
        "Важно! Формат: дд.мм.гггг"
    ]))
    return State.EXPIRATION_DATE

async def get_event_expiration_date(update: Update, context: CustomContext):
    try:
        iso_date = date.fromisoformat("-".join(update.message.text.split('.')[::-1]))
    except ValueError:
        await update.message.reply_text("Формат: дд.мм.гггг")
        return
    context.user_data['expiration_date'] = str(iso_date)
    await update.message.reply_text("Подробное описание и любые комментарии, которые стоит знать интересующимся:")
    return State.DESCRIPTION

async def get_event_description(update: Update, context: CustomContext):
    context.user_data['description'] = update.message.text_html
    txt = "\n".join([
        "Проверьте, всё правильно? Ваше мероприятие будет отправлено на проверку",
        "",
        f"<b>Название</b>: {context.user_data["event_name"]}",
        f"<b>Место</b>: {context.user_data["location"]}",
        f"<b>Время</b>: {context.user_data["datetime"]}",
        f"<b>Годен до:</b> {context.user_data["expiration_date"]}",
        f"<b>Описание</b>: {context.user_data["description"]}"
    ])
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Да, всё верно", callback_data="confirm_event"),
        InlineKeyboardButton("Нет, хочу кое-что изменить", callback_data="edit_event")
    ]])
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.CONFIRM_EVENT

async def confirm_event(update: Update, context: CustomContext):
    await update.callback_query.answer("Мероприятие отправлено на проверку!")
    event = {
        "event_name": context.user_data["event_name"],
        "location": context.user_data["location"],
        "datetime": context.user_data["datetime"],
        "expiration_date": context.user_data["expiration_date"],
        "description": context.user_data["description"],
        "author": update.effective_user.id,
        "status": "pending",
    }
    txt = "\n".join([
        "Ваше мероприятие отправлено на проверку! ❤️",
        "",
        f"<b>Название</b>: {event["event_name"]}",
        f"<b>Место</b>: {event["location"]}",
        f"<b>Время</b>: {event["datetime"]}",
        f"<b>Годен до:</b> {event["expiration_date"]}",
        f"<b>Описание</b>: {event["description"]}"
    ])
    await update.callback_query.edit_message_text(txt, parse_mode=ParseMode.HTML)

    event_id = context.database.next_event_id()
    context.database.data["events"][event_id] = event
    context.database.save()

    username = update.effective_user.username
    name = update.effective_user.full_name
    keyboard = [[
        InlineKeyboardButton("Принять", callback_data=EventVerdict(event_id, accept=True)),
        InlineKeyboardButton("Отклонить", callback_data=EventVerdict(event_id, accept=False))
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = "\n".join([
        f"@{username} - {name} хочет предложить мероприятие (id:{event_id}):",
        f"<b>Название</b>: {event["event_name"]}",
        f"<b>Место</b>: {event["location"]}",
        f"<b>Время</b>: {event["datetime"]}",
        f"<b>Годен до:</b> {event["expiration_date"]}",
        f"<b>Описание</b>: {event["description"]}"
    ])
    await context.bot.send_message(
        chat_id=int(context.config["ADMIN_CHAT_ID"]), 
        text=msg, 
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

async def cancel_event_creation(update: Update, context: CustomContext):
    await update.message.reply_text("Создание мероприятия отменено")
    context.user_data.clear()
    return ConversationHandler.END

async def event_verdict(update: Update, context: CustomContext):
    await update.callback_query.answer()
    verdict = update.callback_query.data

    db = context.database
    event = db.data["events"][str(verdict.event_id)]
    msg_admin = f"Мероприятие \"{event["event_name"]}\" (id: {verdict.event_id}) "
    if verdict.accept:
        db.data["events"][str(verdict.event_id)]["status"] = "active"
        msg_admin += "принято ✅"
    else:
        db.data["events"][str(verdict.event_id)]["status"] = "declined"
        msg_admin += "отклонено ❌"
    db.save()
    await update.callback_query.edit_message_text(msg_admin)
    await context.bot.send_message(event["author"], msg_admin)

async def list_events(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(None)
    if (~MemberFilter(context.database)).check_update(update):
        await update.effective_message.reply_text("Зарегистрируйтесь через /register, чтобы создать мероприятие")
        return
    
    events_list = context.get_events(update.effective_user.id)
    keyboard = []
    for (event_id, event) in events_list.items():
        readable_status = get_readable_status(event["status"])
        event_name_clean = re.sub(r'<[^<]+?>', "", event["event_name"])
        event_name = event_name_clean[:25] + ("..." if len(event_name_clean) >= 25 else '')
        keyboard.append([
            InlineKeyboardButton(
                f"({readable_status[-1]}) [{event_id}] {event_name}",
                callback_data=ManageEvent(event_id)
            )
        ])
    if update.callback_query:
        await update.callback_query.from_user.send_message(
            "Список доступных мероприятий:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "Список доступных мероприятий:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

async def list_every_event(update: Update, context: CustomContext) -> None:
    if not filters.Chat(int(context.config["OWNER"])).check_update(update):
        await update.effective_message.reply_text("Нет прав администратора бота")
        return
    events_list = context.get_events(update.effective_user.id, filter_available=False)
    keyboard = []
    for (event_id, event) in events_list.items():
        readable_status = get_readable_status(event["status"])
        event_name_clean = re.sub(r'<[^<]+?>', "", event["event_name"])
        event_name = event_name_clean[:25] + ("..." if len(event_name_clean) >= 25 else '')
        keyboard.append([
            InlineKeyboardButton(
                f"({readable_status[-1]}) [{event_id}] {event_name}",
                callback_data=ManageEvent(event_id)
            )
        ])
    if update.callback_query:
        await update.callback_query.from_user.send_message(
            "Список ВСЕХ мероприятий:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "Список ВСЕХ мероприятий:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    

async def manage_event(update: Update, context: CustomContext):
    if not update.callback_query:
        return
    await update.callback_query.answer()
    event_id = update.callback_query.data.event_id
    event = context.database.data["events"][event_id]
    
    author_username = context.database.data["members"][str(event["author"])]["username"]
    txt = "\n".join([
        f"Организатор: {author_username}",
        "",
        f"<b>Название</b>: {event["event_name"]}",
        f"<b>Место</b>: {event["location"]}",
        f"<b>Время</b>: {event["datetime"]}",
        f"<b>Годен до:</b> {event["expiration_date"]}",
        f"<b>Описание</b>: {event["description"]}",
        "",
        f"Статус: {get_readable_status(event["status"])}"
    ])
    await update.callback_query.from_user.send_message(txt, parse_mode=ParseMode.HTML)

