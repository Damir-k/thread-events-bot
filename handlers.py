from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton,
    KeyboardButton)
from telegram.constants import ParseMode
from telegram.ext import filters

from custom_context import CustomContext
from dynamic_filters import MemberFilter, PendingFilter
from callback_types import RegisterVerdict

from uuid import uuid4


async def start(update: Update, context: CustomContext):
    user = update.effective_user
    context.database.save_id(user.username, user.id)
    status = context.get_user_status(user.id)
    msg = f"<b>Привет! Если ты это читаешь, значит бот сейчас в активной разработке! :)</b>"
    msg += f"\n<b>Статус:</b> {status}"
    keyboard = []
    if (~MemberFilter(context.database) & ~PendingFilter(context.database)).check_update(update):
        keyboard.append([InlineKeyboardButton(
            "Зарегистрироваться", 
            callback_data="register"
        )])
    if MemberFilter(context.database).check_update(update):
        number_events = len(context.get_events(user.id))
        badge = context.get_badge(number_events)
        msg += f"\n<b>Мероприятия:</b> {number_events} {badge}"
        msg += f"\n - Создать новое мероприятие: /new_event"
        msg += f"\n - Список мероприятий: /list_events"
        keyboard.append([InlineKeyboardButton(
            "Создать новое мероприятие",
            callback_data="new_event"
        ), InlineKeyboardButton(
            "Список мероприятий",
            callback_data="list_events"
        )])
    markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(text=msg, parse_mode=ParseMode.HTML, reply_markup=markup)

async def register(update: Update, context: CustomContext):
    user_id = update.effective_user.id
    if PendingFilter(context.database).check_update(update):
        await context.bot.send_message(user_id, "Ваша заявка рассматривается! Подождите, пожалуйста")
        return
    if MemberFilter(context.database).check_update(update):
        await context.bot.send_message(user_id, "Вы уже зарегистрированы! /start для главного меню")
        return
    
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)
        await update.callback_query.answer("Заявка отправлена!")
    else:
        msg = "Ваша заявка отправлена на рассмотрение! Ожидайте в скором времени получить полный доступ к мероприятиям Нити!"
        await context.bot.send_message(user_id, text=msg)
    
    # отправляем тикет в канал
    username = update.effective_user.username
    name = update.effective_user.full_name
    keyboard = [[
        InlineKeyboardButton("Принять", callback_data=RegisterVerdict(user_id, accept=True)),
        InlineKeyboardButton("Отклонить", callback_data=RegisterVerdict(user_id, accept=False))
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = f"@{username} - {name} хочет получить доступ к мероприятиям Нити"
    await context.bot.send_message(chat_id=int(context.config["ADMIN_CHAT_ID"]), text=msg, reply_markup=markup)
    context.database.save_entry("pending", user_id, username, name)

async def register_verdict(update: Update, context: CustomContext) -> None:
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    db = context.database
    user_id = str(query.data.user_id)
    username = db.data["pending"][user_id]["username"]
    name = db.data["pending"][user_id]["name"]
    if query.data.accept:
        db.data["members"][user_id] = db.data["pending"][user_id]
        db.save()
        await query.edit_message_text(text=f"{username} - {name} зарегистрирован(а)! ✅\nПроверил(а): @{query.from_user.username}")
        msg = "Поздравляем! Вам теперь доступны мероприятия Нити!"
    else:
        await query.edit_message_text(text=f"Заявка {username} - {name} отклонена! ❌\nПроверил(а): @{query.from_user.username}")
        msg = "Ваша заявка была отклонена. Если вы считаете это ошибкой, подайте её заново"
    db.delete_entry("pending", user_id)
    await context.bot.send_message(user_id, text=msg)

async def admin(update: Update, context: CustomContext) -> None:
    if not filters.Chat(int(context.config["OWNER"])).check_update(update):
        await update.effective_message.reply_text("Нет прав администратора бота")
        return
    
    help_msg = "Использование `/admin`:\n \
        `/admin <add/remove> <table> <username>`\n \
        `/admin <print/remove> <table>`\n \
        `/admin <print>`"
    args = context.args
    if not args:
        await update.effective_message.reply_text(help_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    if args[0] == "add":
        if len(args) == 3:
            _, table, username = args
            if username.strip("@") not in context.database.data["ids"]:
                msg = f"{username} не существует в таблице ids!"
            else:
                chat_id = context.database.data["ids"][username.strip("@")]
                name = (await context.bot.get_chat(chat_id)).full_name
                context.database.save_entry(table, chat_id, username.strip("@"), name)
                msg = f"{username} - {name} добавлен(а) к {table}"
            await update.effective_message.reply_text(msg)
            return
    if args[0] == "print":
        if len(args) == 1:
            await update.effective_message.reply_text(
                f"Доступные таблицы:\n```json\n{list(context.database.data.keys())}```", 
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        if len(args) == 2:
            _, table = args
            await update.effective_message.reply_text(
                f"Таблица `{table}`:\n```json\n{context.database.data[table]}```", 
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
    if args[0] == "remove":
        # if len(args) == 2:
        #     _, table = args
        #     if table not in context.database.data:
        #         msg = "Такой таблицы не существует. `/admin print` для списка таблиц"
        #     else:
        #         context.database.data[table] = dict()
        #         msg = f"`{table}` удалена"
        #     await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
        #     return
        if len(args) == 3:
            _, table, username = args
            if username.strip("@") not in context.database.data["ids"]:
                msg = f"{username} не существует в таблице ids!"
            else:
                chat_id = context.database.data["ids"][username.strip("@")]
                name = (await context.bot.get_chat(chat_id)).full_name
                context.database.delete_entry(table, chat_id)
                msg = f"{username} - {name} удален(а) из {table}"
            await update.effective_message.reply_text(msg)
            return
    
    await update.effective_message.reply_text(help_msg, parse_mode=ParseMode.MARKDOWN_V2)
    return

async def inline_sharing(update: Update, context: CustomContext):
    if not MemberFilter(context.database).check_update(update):
        await update.inline_query.answer([], is_personal=True, cache_time=60, button=InlineQueryResultsButton(
            "Зарегистрироваться в боте...",
            start_parameter="register"
        ))
        return

    query = update.inline_query.query
    if not query:
        results = [InlineQueryResultArticle(
            id=str(uuid4()),
            title=f'Мероприятие {i}',
            input_message_content=InputTextMessageContent(f"Хорошее меро №{i}")
        )      
        for i in range(1,5)]
    else:
        results = []
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title='Создать новое мероприятие...',
                input_message_content=InputTextMessageContent(f"Новое меро: {query}")
            )
        )
    await context.bot.answer_inline_query(update.inline_query.id, results, is_personal=True)


async def invalid_callback(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)
