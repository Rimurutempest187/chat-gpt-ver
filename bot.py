# bot.py
import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PollAnswerHandler
import config
import db

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Helpers ---
def is_admin(user_id):
    return user_id in config.ADMIN_IDS

async def check_admin(update: Update) -> bool:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ဤ Command ကို Admin သာ အသုံးပြုနိုင်ပါသည်။")
        return False
    return True

# --- User Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or user.first_name)
    msg = f"🙏 မင်္ဂလာပါ {user.first_name}။ Church Community Bot မှ ကြိုဆိုပါတယ်။\n"
    msg += "အသုံးပြုနည်းကို သိရှိလိုပါက /help ကို နှိပ်ပါ။\n\n"
    msg += "Create by : @Enoch_777"
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
📖 **Bot အသုံးပြုနည်း လမ်းညွှန်**
/start - Bot ကို စတင်ရန်
/about - သမိုင်းကြောင်းနှင့် ရည်ရွယ်ချက်
/contact - တာဝန်ခံများ၏ ဖုန်းနံပါတ်များ
/verse - ယနေ့အတွက် ဖတ်ရန်ကျမ်းချက်
/events - လာမည့် အသင်းတော်အစီအစဉ်များ
/birthday - မွေးနေ့ရှင်များ
/pray <စာသား> - ဆုတောင်းခံရန်
/praylist - ဆုတောင်းခံချက်စာရင်း
/quiz - ကျမ်းစာဉာဏ်စမ်း
/Tops - အမှတ်အများဆုံး စာရင်း
/report <စာသား> - သတင်းပို့ရန်
"""
    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(db.get_setting("about", "သမိုင်းကြောင်း မရှိသေးပါ။"))

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(db.get_setting("contact", "ဆက်သွယ်ရန် မရှိသေးပါ။"))

async def show_verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(db.get_setting("verse", "ယနေ့ ကျမ်းချက် မရှိသေးပါ။"))

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(db.get_setting("events", "လာမည့် အစီအစဉ် မရှိသေးပါ။"))

async def show_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(db.get_setting("birthday", "ယခုလ မွေးနေ့ရှင်စာရင်း မရှိသေးပါ။"))

async def pray_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("ကျေးဇူးပြု၍ /pray နောက်တွင် ဆုတောင်းပေးစေလိုသော အချက်များကို ရေးပါ။")
        return
    username = update.effective_user.username or update.effective_user.first_name
    db.add_prayer(username, text)
    await update.message.reply_text("🙏 ဆုတောင်းခံချက်ကို လက်ခံရရှိပါပြီ။")

async def pray_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prayers = db.get_prayers()
    if not prayers:
        await update.message.reply_text("လက်ရှိတွင် ဆုတောင်းခံချက် မရှိသေးပါ။")
        return
    msg = "🙏 **ဆုတောင်းခံချက်များ**\n\n"
    for p in prayers:
        msg += f"👤 @{p[0]}: {p[1]}\n\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # နမူနာ Quiz (Data ကို Database ထဲတွင်လည်း သိမ်းနိုင်သည်)
    question = "ကမ္ဘာဦးကျမ်း ကို ဘယ်သူရေးသားခဲ့သလဲ?"
    options = ["မောရှေ", "ဒါဝိဒ်", "ရှောလမုန်", "ပေါလု"]
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options,
        type=Poll.QUIZ,
        correct_option_id=0,
        is_anonymous=False
    )

async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if answer.option_ids[0] == 0: # မှန်ကန်သောအဖြေ Index ဆိုလျှင်
        db.add_score(answer.user.id)

async def top_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tops = db.get_top_scores()
    msg = "🏆 **Quiz Top Scores**\n\n"
    for idx, (name, score) in enumerate(tops):
        msg += f"{idx+1}. {name} - {score} marks\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("ကျေးဇူးပြု၍ /report နောက်တွင် အကြောင်းအရာရေးပါ။")
        return
    # Report ကို Admin ဆီပို့ရန်
    for admin in config.ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin, text=f"🔔 Report from {update.effective_user.first_name}:\n{text}")
        except:
            pass
    await update.message.reply_text("✅ Report ပေးပို့ပြီးပါပြီ။")

# --- Admin Commands ---
async def edit_setting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, success_msg: str):
    if not await check_admin(update): return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("ကျေးဇူးပြု၍ စာသားထည့်ပါ။ ဥပမာ - /eabout အကြောင်းအရာ...")
        return
    db.update_setting(key, text)
    await update.message.reply_text(success_msg)

async def eabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await edit_setting_cmd(update, context, "about", "✅ သမိုင်းကြောင်း ပြင်ဆင်ပြီးပါပြီ။")

async def econtact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await edit_setting_cmd(update, context, "contact", "✅ ဖုန်းနံပါတ်များ ပြင်ဆင်ပြီးပါပြီ။")

async def everse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await edit_setting_cmd(update, context, "verse", "✅ ယနေ့ကျမ်းချက် ပြင်ဆင်ပြီးပါပြီ။")

async def eevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await edit_setting_cmd(update, context, "events", "✅ အစီအစဉ်များ ပြင်ဆင်ပြီးပါပြီ။")

async def ebirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await edit_setting_cmd(update, context, "birthday", "✅ မွေးနေ့ရှင်စာရင်း ပြင်ဆင်ပြီးပါပြီ။")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    if not update.message.reply_to_message:
        await update.message.reply_text("ကျေးဇူးပြု၍ Broadcast လုပ်လိုသော စာ (သို့) ပုံကို Reply ပြန်ပြီး /broadcast ဟုရိုက်ပါ။")
        return
    
    users = db.get_all_users()
    count = 0
    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id)
            count += 1
        except Exception:
            pass # User blocks the bot
    await update.message.reply_text(f"✅ လူပေါင်း {count} ဦးထံသို့ ပေးပို့ပြီးပါပြီ။")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    users = db.get_all_users()
    await update.message.reply_text(f"📊 လက်ရှိ Bot အသုံးပြုသူ စုစုပေါင်း: {len(users)} ယောက်။")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    db.backup_db()
    await update.message.reply_text("✅ Database ကို Backup ပြုလုပ်ပြီးပါပြီ။")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    if db.restore_db():
        await update.message.reply_text("✅ Data များကို Restore ပြန်လုပ်ပြီးပါပြီ။")
    else:
        await update.message.reply_text("❌ Backup file မတွေ့ပါ။")

async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    db.clear_all()
    await update.message.reply_text("⚠️ Data အားလုံးကို ဖျက်ပစ်လိုက်ပါပြီ။")

def main():
    db.init_db() # Initialize Database
    app = Application.builder().token(config.BOT_TOKEN).build()

    # User Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", show_about))
    app.add_handler(CommandHandler("contact", show_contact))
    app.add_handler(CommandHandler("verse", show_verse))
    app.add_handler(CommandHandler("events", show_events))
    app.add_handler(CommandHandler("birthday", show_birthday))
    app.add_handler(CommandHandler("pray", pray_request))
    app.add_handler(CommandHandler("praylist", pray_list))
    app.add_handler(CommandHandler("quiz", send_quiz))
    app.add_handler(PollAnswerHandler(receive_quiz_answer))
    app.add_handler(CommandHandler("Tops", top_scores))
    app.add_handler(CommandHandler("report", report))

    # Admin Handlers
    app.add_handler(CommandHandler("eabout", eabout))
    app.add_handler(CommandHandler("econtact", econtact))
    app.add_handler(CommandHandler("everse", everse)) # Added /everse for completeness
    app.add_handler(CommandHandler("eevents", eevents))
    app.add_handler(CommandHandler("ebirthday", ebirthday))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("allclear", allclear))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
