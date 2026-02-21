import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import BOT_TOKEN
from db import init_db
import handlers as H

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

init_db()

app = ApplicationBuilder().token(BOT_TOKEN).build()

# Basic commands
app.add_handler(CommandHandler("start", H.start))
app.add_handler(CommandHandler("help", H.help_cmd))
app.add_handler(CommandHandler("about", H.about))
app.add_handler(CommandHandler("contact", H.contact))
app.add_handler(CommandHandler("verse", H.verse))
app.add_handler(CommandHandler("events", H.events_cmd))
app.add_handler(CommandHandler("birthday", H.birthday))
app.add_handler(CommandHandler("pray", H.pray))
app.add_handler(CommandHandler("praylist", H.praylist))
app.add_handler(CommandHandler("quiz", H.quiz_cmd))
app.add_handler(CallbackQueryHandler(H.quiz_callback, pattern=r"^quiz\|"))
app.add_handler(CommandHandler("Tops", H.tops))
app.add_handler(CommandHandler("report", H.report_cmd))
app.add_handler(CommandHandler("backup", H.backup_cmd))
app.add_handler(CommandHandler("restore", H.restore_cmd))
app.add_handler(CommandHandler("allclear", H.allclear_cmd))
app.add_handler(CommandHandler("stats", H.stats))
# Admin broadcast conversation
from telegram.ext import ConversationHandler
broadcast_conv = ConversationHandler(
    entry_points=[CommandHandler("broadcast", H.broadcast_start)],
    states={0: [MessageHandler(filters.ALL & ~filters.COMMAND, H.broadcast_receive)]},
    fallbacks=[]
)
app.add_handler(broadcast_conv)

# eabout conv
eabout_conv = ConversationHandler(
    entry_points=[CommandHandler("eabout", H.eabout_start)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, H.eabout_receive)]},
    fallbacks=[]
)
app.add_handler(eabout_conv)

# econtact conv
econtact_conv = ConversationHandler(
    entry_points=[CommandHandler("econtact", H.econtact_start)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, H.econtact_receive)]},
    fallbacks=[]
)
app.add_handler(econtact_conv)

# eevents conv
eevents_conv = ConversationHandler(
    entry_points=[CommandHandler("eevents", H.eevents_start)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, H.eevents_receive)]},
    fallbacks=[]
)
app.add_handler(eevents_conv)

# ebirthday conv
ebirthday_conv = ConversationHandler(
    entry_points=[CommandHandler("ebirthday", H.ebirthday_start)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, H.ebirthday_receive)]},
    fallbacks=[]
)
app.add_handler(ebirthday_conv)

# unknown handler
app.add_handler(MessageHandler(filters.COMMAND, H.unknown))

if __name__ == "__main__":
    print("Bot starting...")
    app.run_polling()
