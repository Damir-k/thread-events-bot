from telegram.ext import (ApplicationBuilder, CommandHandler, 
    CallbackQueryHandler, InlineQueryHandler, ContextTypes, filters, 
    InvalidCallbackData, ConversationHandler, MessageHandler)

import logging
from dotenv import dotenv_values

from handlers import (start, register, register_verdict, 
    admin, inline_sharing, invalid_callback)
from event_handlers import (new_event, list_events, get_event_name, 
    get_event_location, get_event_datetime, get_event_description, confirm_event,
    cancel_event_creation, event_verdict, get_event_expiration_date, manage_event,
    list_every_event)

from custom_context import CustomContext, State
from callback_types import RegisterVerdict, EventVerdict, ManageEvent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
TOKEN = dotenv_values(".env")["TOKEN"]


def main(token):
    context_types = ContextTypes(context=CustomContext)
    application = ApplicationBuilder()\
        .token(f'{token}')\
        .context_types(context_types)\
        .arbitrary_callback_data(True)\
        .concurrent_updates(False)\
        .build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("admin", admin, ~filters.UpdateType.EDITED))
    
    application.add_handlers([
        CommandHandler('register', register),
        CallbackQueryHandler(register, pattern=r'^register$')
    ])

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("new_event", new_event), CallbackQueryHandler(new_event, pattern=r"^new_event$")],
        states={
            State.EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_name)],
            State.LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_location)],
            State.DATE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_datetime)],
            State.EXPIRATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_expiration_date)],
            
            State.DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_description)],
            State.CONFIRM_EVENT: [
                CallbackQueryHandler(confirm_event, pattern=r"^confirm_event$"),
                CallbackQueryHandler(new_event, pattern=r"^edit_event$")
            ]
        },
        fallbacks=[CommandHandler("cancel_event_creation", cancel_event_creation)]
    ))
    application.add_handler(CallbackQueryHandler(event_verdict, EventVerdict))
    application.add_handler(CallbackQueryHandler(manage_event, ManageEvent))

    application.add_handlers([
        CommandHandler("list_events", list_events),
        CallbackQueryHandler(list_events, pattern=r"^list_events$")
    ])
    application.add_handler(CommandHandler(["list_all_events", "list_every_event"], list_every_event))

    application.add_handler(CallbackQueryHandler(register_verdict, RegisterVerdict))
    application.add_handler(CallbackQueryHandler(invalid_callback, InvalidCallbackData))


    application.add_handler(InlineQueryHandler(inline_sharing))

    application.run_polling()


if __name__ == '__main__':
    main(TOKEN)