from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from custom_context import CustomContext
from dynamic_filter import RegisterFilter


async def start(update: Update, context: CustomContext):
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