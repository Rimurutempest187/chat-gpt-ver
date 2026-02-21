# bot.py
import os
import logging
from telegram.ext import ApplicationBuilder
import asyncio
import db, handlers, utils
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var required")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def main():
    await db.init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    handlers.register(app.dispatcher)
    # start polling
    logging.info("Starting bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # idle
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
