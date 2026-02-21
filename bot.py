# bot.py
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config
from db import init_db, get_conn
import handlers
from pathlib import Path

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    init_db()
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("about", handlers.about))
    app.add_handler(CommandHandler("edabout", handlers.edabout))
    app.add_handler(CommandHandler("contact", handlers.contact))
    app.add_handler(CommandHandler("edcontact", handlers.edcontact))
    app.add_handler(CommandHandler("verse", handlers.verse))
    app.add_handler(CommandHandler("edverse", handlers.edverse))
    app.add_handler(CommandHandler("events", handlers.events))
    app.add_handler(CommandHandler("edevents", handlers.edevents))
    app.add_handler(CommandHandler("birthday", handlers.birthday))
    app.add_handler(CommandHandler("edbirthday", handlers.edbirthday))
    app.add_handler(CommandHandler("pray", handlers.pray))
    app.add_handler(CommandHandler("praylist", handlers.praylist))
    app.add_handler(CommandHandler("quiz", handlers.quiz))
    app.add_handler(CommandHandler("edquiz", handlers.edquiz))
    app.add_handler(CommandHandler("tops", handlers.tops))
    app.add_handler(CommandHandler("broadcast", handlers.broadcast))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("report", handlers.report))
    app.add_handler(CommandHandler("backup", handlers.backup))
    app.add_handler(CommandHandler("restore", handlers.restore))
    app.add_handler(CommandHandler("allclear", handlers.allclear))

    # Generic text handler (for quiz answers and fallback)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.handle_text))

    # Track groups when bot added or receives message in group
    async def track_groups(update, context):
        chat = update.effective_chat
        if chat and chat.type in ("group","supergroup"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO groups (id, title) VALUES (?, ?)", (chat.id, chat.title or ""))
            conn.commit()
            conn.close()
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, track_groups))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
