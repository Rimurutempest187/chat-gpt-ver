import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import handlers
import utils

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
DB_PATH = os.getenv("DB_PATH", "data/church.db")

# parse admins
if ADMIN_IDS_STR:
    utils.ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()]
else:
    utils.ADMIN_IDS = []

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # init DB
    await handlers.init(DB_PATH)

    # commands
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))

    app.add_handler(CommandHandler("eabout", handlers.eabout))
    app.add_handler(CommandHandler("about", handlers.about))

    app.add_handler(CommandHandler("contact", handlers.contact))
    app.add_handler(CommandHandler("econtact", handlers.econtact))

    app.add_handler(CommandHandler("verse", handlers.verse))

    app.add_handler(CommandHandler("events", handlers.events))
    app.add_handler(CommandHandler("eevents", handlers.eevents))

    app.add_handler(CommandHandler("birthday", handlers.birthday))
    app.add_handler(CommandHandler("ebirthday", handlers.ebirthday))

    app.add_handler(CommandHandler("pray", handlers.pray))
    app.add_handler(CommandHandler("praylist", handlers.praylist))

    app.add_handler(CommandHandler("quiz", handlers.quiz))
    app.add_handler(CallbackQueryHandler(handlers.callback_query_handler))
    app.add_handler(CommandHandler("Tops", handlers.tops))

    app.add_handler(CommandHandler("broadcast", handlers.broadcast))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("report", handlers.report))
    app.add_handler(CommandHandler("backup", handlers.backup_cmd))
    app.add_handler(CommandHandler("restore", handlers.restore_cmd))
    app.add_handler(CommandHandler("allclear", handlers.allclear))

    async def unknown(update, context):
        await update.message.reply_text("Unknown command. Use /help")

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Bot starting...")

    # ✅ THIS IS THE CORRECT WAY
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
