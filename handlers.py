from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters

from custom_context import CustomContext
from dynamic_filter import RegisterFilter


async def start(update: Update, context: CustomContext):
    user = update.effective_user
    context.database.save_id(user.username, user.id)
    msg = "Привет! Если ты это читаешь, значит бот сейчас в активной разработке! :)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

async def register(update: Update, context: CustomContext):
    usr = update.effective_user.username
    name = update.effective_user.full_name
    chat_id = update.effective_chat.id
    filter_can_register = RegisterFilter(context.database)
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
    
    args = context.args
    if not args:
        msg = "Использование:\n`/admin <add/remove> <table> <username>`\n`/admin <print/remove> <table>`"
        await update.effective_message.reply_text(msg)
        return

    if args[0] == "add":
        if len(args) == 3:
            _, table, username = args
            chat_id = context.database.data["ids"][username.strip("@")]
            name = (await context.bot.get_chat(chat_id)).full_name
            context.database.save_entry(table, chat_id, username.strip("@"), name)
            await update.effective_message.reply_text(f"{username} - {name} добавлен(а) к {table}")
            return
    if args[0] == "print":
        if len(args) == 2:
            _, table = args
            await update.effective_message.reply_text(f"```{context.database.data[table]}```")
            return
    if args[0] == "remove":
        if len(args) == 2:
            _, table = args
            context.database.data[table] = dict()
            await update.effective_message.reply_text(f"{table} удалена")
            return
        if len(args) == 3:
            _, table, username = args
            chat_id = context.database.data["ids"][username.strip("@")]
            context.database.delete_entry(table, chat_id)
            await update.effective_message.reply_text(f"{username} - {name} удален(а) из {table}")
            return
    
    msg = "Использование:\n`/admin <add/remove> <table> <username>`\n`/admin <print/remove> <table>`"
    await update.effective_message.reply_text(msg)
    return
