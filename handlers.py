from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton)
from telegram.constants import ParseMode
from telegram.ext import filters

from custom_context import CustomContext
from dynamic_filter import MemberFilter, PendingFilter

from uuid import uuid4


async def start(update: Update, context: CustomContext):
    user = update.effective_user
    context.database.save_id(user.username, user.id)
    status = context.get_user_status(user.id)
    number_events = len(context.get_events(user.id))
    badge = context.get_badge(number_events)
    msg = f"<b>Привет! Если ты это читаешь, значит бот сейчас в активной разработке! :)</b> \
    \n<b>Статус:</b> {status} \
    \n<b>Мероприятия:</b> {number_events} {badge} \
    \n - Создать новое мероприятие: /new_event"
    await update.effective_message.reply_text(text=msg, parse_mode=ParseMode.HTML)

async def register(update: Update, context: CustomContext):
    usr = update.effective_user.username
    name = update.effective_user.full_name
    chat_id = update.effective_chat.id
    filter_can_register = ~MemberFilter(context.database) & ~PendingFilter(context.database)
    if not filter_can_register.check_update(update):
        await context.bot.send_message(chat_id, "Вы не можете отправить еще одну заявку")
        return
    
    msg = "Ваша заявка отправлена на рассмотрение! Ожидайте в скором времени получить полный доступ к мероприятиям Нити!"
    await context.bot.send_message(chat_id, text=msg)
    keyboard = [
        [InlineKeyboardButton("Принять", callback_data=f"accept;{usr};{name};{chat_id}")],
        [InlineKeyboardButton("Отклонить", callback_data=f"decline;{chat_id}")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = f"@{usr} - {name} хочет получить доступ к мероприятиям Нити"
    await context.bot.send_message(chat_id=int(context.config["ADMIN_CHANNEL_ID"]), text=msg, reply_markup=markup)
    context.database.save_entry("pending", chat_id, usr, name)

async def inline_button(update: Update, context: CustomContext) -> None:
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    
    if query.data.startswith("accept"):
        _, usr, name, chat_id = query.data.split(";")
        await query.edit_message_text(text=f"@{usr} - {name} зарегистрирован(а)!\nПроверил(а): @{query.from_user.username}")
        msg = "Поздравляем! Вам теперь доступны меропирятия Нити!"
        await context.bot.send_message(chat_id, text=msg)
        context.database.save_entry("members", chat_id, usr, name)
        context.database.delete_entry("pending", chat_id)
    elif query.data.startswith("decline"):
        _, chat_id = query.data.split(";")
        await query.delete_message()
        context.database.delete_entry("pending", chat_id)
        msg = "Ваша заявка была отклонена. Если вы считаете это ошибкой, напишите @damirablv"
        await context.bot.send_message(chat_id, text=msg)

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