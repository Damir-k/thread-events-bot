from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, filters

from datetime import date
import re

from custom_context import CustomContext, State, ExactMessages
from dynamic_filters import MemberFilter
from callback_types import EventVerdict, ShowEvent, ManageEvent, EditEvent

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
            readable_status = "Скрыто 🥷"
        case "cool":
            readable_status = "Улыбается 😼"
        case _:
            readable_status = "??? Поздравляю вы сломали бота, напишите @damirablv ☢️"
    return readable_status

def get_event_summary(event: dict) -> str:
    summary = "\n".join([
        f"<b>Название:</b> {event.setdefault("event_name", "-")}",
        f"<b>Место:</b> {event.setdefault("location", "-")}",
        f"<b>Время:</b> {event.setdefault("datetime", "-")}",
        f"<b>Возраст:</b> {event.setdefault("age", "-")}",
        f"<b>Кол-во человек:</b> {event.setdefault("size", "-")}",
        f"<b>Годен до:</b> {event.setdefault("expiration_date", "0001-01-01")}",
        f"<b>Описание:</b> {event.setdefault("description", "-")}",
    ])
    return summary

async def new_event(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(None)
        await update.effective_user.send_message(
            text="<i>Готовимся к созданию...</i>", 
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )
    if (~MemberFilter(context.database)).check_update(update):
        await update.effective_message.reply_text("Зарегистрируйтесь через /register, чтобы создать мероприятие")
        return ConversationHandler.END
    context.logger.warning(f"@{update.effective_user.username} creating event")
    new_event_text = "\n".join([
        "<b>Ура! Создаём новое событие</b> 😌 ",
        ""
    ])
    mid_txt = "\n".join([
        "Вам нужно будет заполнить несколько полей: ",
        "Название, место, дату/время, дату просрочки, возрастное ограничение, ",
        "количество человек и описание/комментарии",
        "",
        "Не волнуйтесь, вы сможете позже отредактировать эти поля перед отправкой",
        "",
        "<i>Введите короткое название нового мероприятия:</i>"
    ])
    if "event_name" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["event_name"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущее название",
            callback_data="keep_event_name"
        )]]
    else:
        txt = new_event_text + "\n" + mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.EVENT_NAME

async def get_event_name(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущее название сохранено")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['event_name'] = update.message.text_html
    mid_txt = "<i>Введите адрес/местоположение мероприятия в свободном формате:</i>"
    if "location" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["location"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущее место",
            callback_data="keep_location"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.LOCATION

async def get_event_location(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущее место сохранено")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['location'] = update.message.text_html
    mid_txt = "<i>Введите дату/время мероприятия в свободном формате:</i>"
    if "datetime" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["datetime"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущее время",
            callback_data="keep_datetime"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.DATE_TIME

async def get_event_datetime(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущие дата/время сохранены")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['datetime'] = update.message.text_html
    mid_txt = "<i>Введите возрастное граничение в свободном формате:</i>"
    if "age" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["age"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущий возраст",
            callback_data="keep_event_age"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.EVENT_AGE 

async def get_event_age(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущий срок годности сохранен")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['age'] = update.message.text_html
    mid_txt = "<i>Введите планируемое количество человек в свободном формате:</i>"
    if "size" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["size"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущее количество человек",
            callback_data="keep_event_size"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.EVENT_SIZE

async def get_event_size(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущее количетсво человек сохранено")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['size'] = update.message.text_html
    mid_txt = "\n".join([
        "<i>Введите дату, после которой событие уже не актульно:</i>",
        "",
        "(Скорее всего это через 1 день после мероприятия)",
        "Важно! <u>Формат: дд.мм.гггг</u>"
    ])
    if "expiration_date" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["expiration_date"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущий срок годности",
            callback_data="keep_expiration_date"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.EXPIRATION_DATE

async def get_event_expiration_date(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        try:
            iso_date = date.fromisoformat("-".join(update.message.text.split('.')[::-1]))
        except ValueError:
            await update.message.reply_text("<u>Формат: дд.мм.гггг</u>")
            return
        context.user_data['expiration_date'] = str(iso_date)
    mid_txt = "<i>Подробное описание и любые комментарии, которые стоит знать интересующимся:</i>"
    if "description" in context.user_data:
        edit_event_text = f"\n<i>[Сохранено]</i><blockquote>{context.user_data["description"]}</blockquote>"
        txt = mid_txt + "\n" + edit_event_text
        keyboard = [[InlineKeyboardButton(
            "Оставить текущее описание",
            callback_data="keep_description"
        )]]
    else:
        txt = mid_txt
        keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Отменить создание мероприятия", 
        callback_data="cancel_event_creation"
    )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.DESCRIPTION

async def get_event_description(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer("Текущее описание сохранено")
        await update.callback_query.edit_message_reply_markup(None)
    else:
        context.user_data['description'] = update.message.text_html
    txt = "\n".join([
        "Проверьте, всё правильно? Ваше мероприятие будет отправлено на проверку",
        "",
        get_event_summary(context.user_data)
    ])
    keyboard = [[
        InlineKeyboardButton("Да, всё верно", callback_data="confirm_event"),
        InlineKeyboardButton("Нет, хочу кое-что изменить", callback_data="edit_event")
    ],
    [InlineKeyboardButton("Отменить создание мероприятия", callback_data="cancel_event_creation")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    return State.CONFIRM_EVENT

async def confirm_event(update: Update, context: CustomContext):
    await update.callback_query.answer("Мероприятие отправлено на проверку!")
    event = {
        "event_name": context.user_data["event_name"],
        "location": context.user_data["location"],
        "datetime": context.user_data["datetime"],
        "age": context.user_data["age"],
        "size": context.user_data["size"],
        "expiration_date": context.user_data["expiration_date"],
        "description": context.user_data["description"],
        "author": update.effective_user.id,
        "status": "pending",
        "subs": context.user_data.setdefault("subs", [update.effective_user.id])
    }
    event_id = context.user_data.setdefault("event_id", context.database.next_event_id())
    context.user_data.clear()
    txt = "\n".join([
        "Ваше мероприятие отправлено на проверку! ❤️",
        "",
        get_event_summary(event)
    ])
    await update.callback_query.edit_message_text(txt, parse_mode=ParseMode.HTML)
    
    keyboard = [[
        KeyboardButton(ExactMessages.MAIN_MENU.value)
    ]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_user.send_message(
        "Вы можете посмотреть текущие активные мероприятия с помощью /list_events",
        reply_markup=markup
    )

    context.database.data["events"][str(event_id)] = event
    context.database.data["members"][str(update.effective_user.id)]["events"].append(event_id)
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
        "",
        get_event_summary(event)    
    ])
    await context.bot.send_message(
        chat_id=int(context.config["ADMIN_CHAT_ID"]), 
        text=msg, 
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

async def cancel_event_creation(update: Update, context: CustomContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(None)
    context.logger.info(f"@{update.effective_user.username} - Создание мероприятия отменено")
    context.user_data.clear()
    keyboard = [[
        KeyboardButton(ExactMessages.MAIN_MENU.value)
    ]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_user.send_message("Создание мероприятия отменено", reply_markup=markup)
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
    context.logger.info(msg_admin)

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
                callback_data=ShowEvent(event_id)
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
    if not filters.Chat(int(context.config["OWNER_CHAT_ID"])).check_update(update):
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
                callback_data=ShowEvent(event_id)
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

async def event_info(update: Update, context: CustomContext):
    db = context.database
    event_id = update.callback_query.data.event_id
    if event_id not in db.data["events"]:
        await update.callback_query.answer("Мероприятие было удалено", show_alert=True)
        return "Мероприятие было удалено", None
    event = db.data["events"][event_id]
    
    author = str(event["author"])
    author_username = db.data["members"][author]["username"]
    user = str(update.effective_user.id)
    user_subbed = int(event_id) in db.data["members"][user]["events"]
    subbed = db.data["events"][event_id].setdefault("subs", [author])
    txt = "\n".join([
        f"<b>Организатор:</b> {author_username}",
        "",
        get_event_summary(event),
        "",
        f"<b>Статус:</b> {get_readable_status(event["status"])}",
        "",
        f"<i>Вы {'участвуете!' if user_subbed else 'не участвуете'}</i>",
        f"<i>Участников: {len(subbed)}</i>"
    ])
    keyboard = [[InlineKeyboardButton("Показать список участников", 
        callback_data=ManageEvent("show_subs", event_id))]
    ]
    if author != user:
        if user_subbed:
            keyboard.append([InlineKeyboardButton("Отменить участие 🫥", 
                callback_data=ManageEvent("unfollow", event_id))]
            )
        else:
            keyboard.append([InlineKeyboardButton("Участвовать! 😎", 
                callback_data=ManageEvent("follow", event_id))]
            )
    else:
        if event["status"] == "active":
            keyboard.append([InlineKeyboardButton("Скрыть", callback_data=ManageEvent("hide", event_id))])
        elif event["status"] == "inactive":
            keyboard.append([InlineKeyboardButton("Показать", callback_data=ManageEvent("show", event_id))])
        keyboard.append([
            InlineKeyboardButton("Изменить", callback_data=ManageEvent("edit", event_id)),
            InlineKeyboardButton("Удалить", callback_data=ManageEvent("delete", event_id))
        ])
    markup = InlineKeyboardMarkup(keyboard)
    return txt, markup

async def show_event(update: Update, context: CustomContext):
    if not update.callback_query:
        return
    await update.callback_query.answer()
    txt, markup = await event_info(update, context)
    await update.callback_query.from_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)

async def manage_event(update: Update, context: CustomContext):
    if not update.callback_query:
        return
    await update.callback_query.answer()
    query = update.callback_query
    event_id = query.data.event_id
    user_id = query.from_user.id
    action = query.data.action
    db = context.database
    event = db.data["events"][event_id]
    context.logger.info(f"@{query.from_user.username} - manage event {event_id}")

    if action == "show_subs":
        subs = event.setdefault("subs", [event["author"]])
        db.save()
        members_list = [
            f"{db.data["members"][str(sub)]["username"]}: {db.data["members"][str(sub)]["name"]}"
            for sub in subs
        ]
        subs_table = "\n".join(members_list)
        txt = f"<b>Участвуют: {len(members_list)}</b>\n" + subs_table
        await query.from_user.send_message(txt, parse_mode=ParseMode.HTML)
    elif action == "follow":
        db.data["members"][str(user_id)]["events"].append(int(event_id))
        db.data["events"][event_id]["subs"].append(user_id)
        db.save()
        txt, markup = await event_info(update, context)
        await query.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "unfollow":
        followed_events = db.data["members"][str(user_id)]["events"]
        followed_events.pop(followed_events.index(int(event_id)))
        event_subs = db.data["events"][event_id]["subs"]
        event_subs.pop(event_subs.index(user_id))
        db.save()
        txt, markup = await event_info(update, context)
        await query.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "show":
        db.data["events"][event_id]["status"] = "active"
        db.save()
        txt, markup = await event_info(update, context)
        await query.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "hide":
        db.data["events"][event_id]["status"] = "inactive"
        db.save()
        txt, markup = await event_info(update, context)
        await query.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "edit":
        await query.from_user.send_message("\n".join([
            "Если Вы хотите изменить своё мероприятие, вам придется",
            "заново отправлять запрос на его проверку"
        ]), reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Изменить", callback_data=EditEvent("edit", event_id, query.message.chat_id, query.message.message_id)),
            InlineKeyboardButton("Оставить", callback_data=EditEvent("cancel", event_id))
        ]]))
    elif action == "delete":
        await query.from_user.send_message("\n".join([
            "Если Вы хотите УДАЛИТЬ своё мероприятие,",
            "это НАВСЕГДА"
        ]), reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("УДАЛИТЬ", callback_data=EditEvent("delete", event_id, query.message.chat_id, query.message.message_id)),
            InlineKeyboardButton("Оставить", callback_data=EditEvent("cancel", event_id))
        ]]))

async def edit_event(update: Update, context: CustomContext):
    if not update.callback_query:
        return
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    mode = query.data.mode
    event_id = query.data.event_id
    chat_id = query.data.chat_id
    message_id = query.data.message_id
    db = context.database

    if mode == "cancel":
        return
    if mode == "delete":
        context.logger.warning(f"@{query.from_user.username} - delete event {event_id}")
        await context.bot.delete_message(chat_id, message_id)
        event = db.data["events"].pop(event_id)
        db.save()
        await query.from_user.send_message(f"<b>Мероприятие удалено:</b>\n{event["event_name"]}", parse_mode=ParseMode.HTML)
        return
    if mode == "edit":
        context.logger.warning(f"@{query.from_user.username} - edit event {event_id}")
        await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        await update.effective_user.send_message(
            text="<i>Готовимся к изменению...</i>", 
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )
        event = db.data["events"][event_id]
        context.user_data.update(event)
        context.user_data["event_id"] = int(event_id)
        txt = "\n".join([
            "Вам будет предложено изменить следующие поля: ",
            "Название, место, дату/время, дату просрочки, возрастное ограничение, ",
            "количество человек и описание/комментарии",
            "",
            "Не волнуйтесь, вы сможете позже отредактировать эти поля перед отправкой",
            "",
            "<i>Введите короткое название нового мероприятия:</i>",
            "",
            f"<i>[Сохранено]</i><blockquote>{context.user_data["event_name"]}</blockquote>"
        ])
        keyboard = [
            [InlineKeyboardButton("Оставить текущее название", callback_data="keep_event_name")],
            [InlineKeyboardButton("Отменить изменение мероприятия", callback_data="cancel_event_creation")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.effective_user.send_message(txt, parse_mode=ParseMode.HTML, reply_markup=markup)
        return State.EVENT_NAME

