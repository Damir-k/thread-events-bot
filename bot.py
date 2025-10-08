from telegram.ext import (ApplicationBuilder, CommandHandler, 
    CallbackQueryHandler, InlineQueryHandler, ContextTypes, filters, InvalidCallbackData)

import logging
from dotenv import dotenv_values
from typing import Literal, Tuple, Any

from handlers import (start, register, register_verdict, 
    admin, inline_sharing, new_event, invalid_callback)
from custom_context import CustomContext
from callback_types import RegisterVerdict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = dotenv_values(".env")["TOKEN"]
if __name__ == '__main__':
    context_types = ContextTypes(context=CustomContext)
    application = ApplicationBuilder()\
        .token(f'{TOKEN}')\
        .context_types(context_types)\
        .arbitrary_callback_data(True)\
        .build()
    

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("admin", admin, ~filters.UpdateType.EDITED))
    
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CallbackQueryHandler(register, pattern=r'^register$'))

    application.add_handler(CommandHandler("new_event", new_event))
    application.add_handler(CallbackQueryHandler(new_event, pattern=r"^new_event$"))

    application.add_handler(CallbackQueryHandler(register_verdict, RegisterVerdict))
    application.add_handler(CallbackQueryHandler(invalid_callback, InvalidCallbackData))

    application.add_handler(InlineQueryHandler(inline_sharing))

    application.run_polling()