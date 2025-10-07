import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from dotenv import dotenv_values

config = dotenv_values(".env")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Привет! Если ты это читаешь, значит бот сейчас в активной разработке! :)\nИспользуй команду /register, чтобы отправить заявку на доступ к нитевским мероприятиям"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Ваша заявка отправлена на рассмотрение! Ожидайте в скором времени получить полный доступ к мероприятиям Нити!"
    usr = update.effective_user.username
    name = update.effective_user.full_name
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text=msg)
    keyboard = [
        [InlineKeyboardButton("Принять", callback_data=f"accept;{usr};{name};{chat_id}")],
        [InlineKeyboardButton("Отклонить", callback_data=f"decline;{chat_id}")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = f"@{usr} - {name} хочет получить доступ к мероприятиям Нити"
    await context.bot.send_message(chat_id=int(config["ADMIN_CHANNEL_ID"]), text=msg, reply_markup=markup)
    # await ticket.reply_text("Выберете действие:", reply_markup=markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    if query.data.startswith("accept"):
        _, usr, name, chat_id = query.data.split(";")
        await query.edit_message_text(text=f"@{usr} - {name} зарегистрирован(а)!")
        msg = "Поздравляем! Вам теперь доступны меропирятия Нити!"
        await context.bot.send_message(chat_id, text=msg)
    elif query.data.startswith("decline"):
        _, chat_id = query.data.split(";")
        await query.delete_message()
        msg = "Ваша заявка была отклонена. Если вы считаете это ошибкой, напишите @damirablv"
        await context.bot.send_message(chat_id, text=msg)

if __name__ == '__main__':
    application = ApplicationBuilder().token(f'{config["TOKEN"]}').build()
    
    start_handler = CommandHandler('start', start)
    register_handler = CommandHandler('register', register)
    application.add_handler(start_handler)
    application.add_handler(register_handler)
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()