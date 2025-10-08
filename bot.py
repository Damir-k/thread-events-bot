from telegram.ext import (ApplicationBuilder, CommandHandler, 
CallbackQueryHandler, ContextTypes, filters)

import logging
from dotenv import dotenv_values

from handlers import start, register, inline_button, admin
from custom_context import CustomContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = dotenv_values(".env")["TOKEN"]
if __name__ == '__main__':
    context_types = ContextTypes(context=CustomContext)
    application = ApplicationBuilder().token(f'{TOKEN}').context_types(context_types).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CallbackQueryHandler(inline_button))
    application.add_handler(CommandHandler("admin", admin, ~filters.UpdateType.EDITED))
    
    application.run_polling()