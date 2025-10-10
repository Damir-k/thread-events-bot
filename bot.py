from telegram.ext import (ApplicationBuilder, CommandHandler, 
    CallbackQueryHandler, InlineQueryHandler, ContextTypes, filters, 
    InvalidCallbackData, ConversationHandler, MessageHandler,
    PicklePersistence)

import logging
from dotenv import dotenv_values
import os, sys

from handlers import (start, register, register_verdict, 
    admin, inline_sharing, invalid_callback, error_handler, restart)
from event_handlers import (new_event, list_events, get_event_name, 
    get_event_location, get_event_datetime, get_event_description, confirm_event,
    cancel_event_creation, event_verdict, get_event_expiration_date, show_event,
    list_every_event, get_event_age, get_event_size, manage_event, edit_event)

from custom_context import CustomContext, State, ExactMessages
from callback_types import RegisterVerdict, EventVerdict, ShowEvent, ManageEvent, EditEvent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
TOKEN = dotenv_values(".env")["TOKEN"]


def main(token):
    my_persistence = PicklePersistence(filepath='picklepersistence')
    context_types = ContextTypes(context=CustomContext)
    application = ApplicationBuilder()\
        .token(f'{token}')\
        .context_types(context_types)\
        .arbitrary_callback_data(True)\
        .concurrent_updates(False)\
        .build()
        # .persistence(my_persistence)\

    application.bot_data["restart"] = False
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("admin", admin, ~filters.UpdateType.EDITED))
    
    application.add_handlers([
        CommandHandler('register', register),
        CallbackQueryHandler(register, pattern=r'^register$')
    ])

    # application.add_handler(CallbackQueryHandler(edit_event, EditEvent))
    application.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_event, EditEvent),
            CommandHandler("new_event", new_event), 
            CallbackQueryHandler(new_event, pattern=r"^new_event$"),
        ],
        states={
            State.EVENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_name),
                CallbackQueryHandler(get_event_name, pattern=r"^keep_event_name$")
            ],
            State.LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_location),
                CallbackQueryHandler(get_event_location, pattern=r"^keep_location$")
            ],
            State.DATE_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_datetime),
                CallbackQueryHandler(get_event_datetime, pattern=r"^keep_datetime$")
            ],
            State.EVENT_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_age),
                CallbackQueryHandler(get_event_age, pattern=r"^keep_event_age$")
            ],
            State.EVENT_SIZE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_size),
                CallbackQueryHandler(get_event_size, pattern=r"^keep_event_size$")
            ],
            State.EXPIRATION_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_expiration_date),     
                CallbackQueryHandler(get_event_expiration_date, pattern=r"^keep_expiration_date$")
            ],
            State.DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_description),
                CallbackQueryHandler(get_event_description, pattern=r"^keep_description$")
            ],
            State.CONFIRM_EVENT: [
                CallbackQueryHandler(confirm_event, pattern=r"^confirm_event$"),
                CallbackQueryHandler(new_event, pattern=r"^edit_event$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel_event_creation", cancel_event_creation),
            CallbackQueryHandler(cancel_event_creation, pattern=r"^cancel_event_creation$")
        ],
        name="event creation"
        # persistent=True
    ))
    application.add_handler(CallbackQueryHandler(event_verdict, EventVerdict))
    application.add_handler(CallbackQueryHandler(show_event, ShowEvent))
    application.add_handler(CallbackQueryHandler(manage_event, ManageEvent))
    application.add_handlers([
        CommandHandler("list_events", list_events),
        CallbackQueryHandler(list_events, pattern=r"^list_events$")
    ])
    application.add_handler(CommandHandler(["list_all_events", "list_every_event"], list_every_event))

    application.add_handler(CallbackQueryHandler(register_verdict, RegisterVerdict))
    application.add_handler(CallbackQueryHandler(invalid_callback, InvalidCallbackData))

    # application.add_handler(InlineQueryHandler(inline_sharing))
    application.add_error_handler(error_handler)
    application.add_handlers([
        CommandHandler('start', start),
        CommandHandler("menu", start),
        MessageHandler(filters.Text([ExactMessages.MAIN_MENU.value]) & ~filters.COMMAND, start)
    ])

    application.run_polling()
    if application.bot_data["restart"]:
        os.system("clear")
        os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == '__main__':
    main(TOKEN)