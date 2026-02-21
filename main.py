# main.py
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from config import BOT_TOKEN, ADMIN_IDS, CREATOR_SIGNATURE, BACKUP_FILE, DB_FILE
import db
import utils
import os
import shutil

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    user = update.effective_user
    chat = update.effective_chat
    db.add_chat(chat.id, chat.type, chat.title, user.username if user else None)
    text = f"မင်္ဂလာပါ {user.first_name if user else ''}!\n\nChurch Community Bot သို့ ကြိုဆိုပါတယ်။\n\n{CREATOR_SIGNATURE}"
    update.message.reply_text(text)

def help_cmd(update, context):
    text = (
        "/start - စတင်အသုံးပြုခြင်း\n"
        "/help - လမ်းညွှန်\n"
        "/about - အသင်းတော်အကြောင်း\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက် (Random)\n"
        "/events - လာမည့် အစီအစဉ်များ\n"
        "/birthday - ယခုလအတွင်း မွေးနေ့များ\n"
        "/pray <text> - ဆုတောင်းပေးရန်\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - ကျမ်းစာ ဉာဏ်စမ်း\n"
        "/Tops - Quiz အမှတ် အများဆုံး\n"
        "/contact - တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/report <text> - သတင်း/အကြောင်းအရာ တင်ပြရန်\n\nAdmin commands:\n"
        "/eabout <text> - about edit\n"
        "/econtact <name>|<phone> - add contact\n"
        "/eevents <title>|<datetime>|<location>|<note> - add event\n"
        "/ebirthday <name>|<day>|<month>|<note> - add birthday\n"
        "/broadcast - reply to a message and send to all chats\n"
        "/stats - usage stats\n"
        "/backup - create and send backup\n"
        "/restore - reply to a DB file to restore\n"
        "/allclear - clear all data\n"
    )
    update.message.reply_text(text)

def about(update, context):
    text = db.get_about()
    update.message.reply_text(text)

def eabout(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    args = context.args
    if not args:
        update.message.reply_text("အသုံး: /eabout <text>")
        return
    new_text = " ".join(args)
    db.set_about(new_text)
    update.message.reply_text("About ကို ပြင်ဆင်ပြီးပါပြီ။")

def contact(update, context):
    rows = db.list_contacts()
    update.message.reply_text(utils.format_contacts(rows))

def econtact(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    text = " ".join(context.args)
    if "|" not in text:
        update.message.reply_text("အသုံး: /econtact <name>|<phone>")
        return
    name, phone = [p.strip() for p in text.split("|",1)]
    db.add_contact(name, phone)
    update.message.reply_text("Contact ထည့်ပြီးပါပြီ။")

def verse(update, context):
    v = db.get_random_verse()
    if v:
        update.message.reply_text(v)
    else:
        update.message.reply_text("ကျမ်းစာ မရှိသေးပါ။")

def events(update, context):
    rows = db.list_events()
    update.message.reply_text(utils.format_events(rows))

def eevents(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    text = " ".join(context.args)
    if "|" not in text:
        update.message.reply_text("အသုံး: /eevents <title>|<datetime>|<location>|<note>")
        return
    title, datetime_str, location, note = [p.strip() for p in text.split("|",3)]
    db.add_event(title, datetime_str, location, note)
    update.message.reply_text("Event ထည့်ပြီးပါပြီ။")

def birthday(update, context):
    # list birthdays for current month
    from datetime import datetime
    month = datetime.now().month
    rows = db.list_birthdays(month)
    update.message.reply_text(utils.format_birthdays(rows))

def ebirthday(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    text = " ".join(context.args)
    if "|" not in text:
        update.message.reply_text("အသုံး: /ebirthday <name>|<day>|<month>|<note>")
        return
    name, day, month, note = [p.strip() for p in text.split("|",3)]
    try:
        day_i = int(day); month_i = int(month)
    except:
        update.message.reply_text("day နှင့် month ကို နံပါတ်ဖြင့် ထည့်ပါ။")
        return
    db.add_birthday(name, day_i, month_i, note)
    update.message.reply_text("Birthday ထည့်ပြီးပါပြီ။")

def pray(update, context):
    user = update.effective_user
    text = " ".join(context.args)
    if not text:
        update.message.reply_text("အသုံး: /pray <text>")
        return
    db.add_prayer(user.id, user.username or user.first_name, text)
    update.message.reply_text("သင့်ဆုတောင်းကို မှတ်တမ်းတင်ပြီးပါပြီ။")

def praylist(update, context):
    rows = db.list_prayers()
    if not rows:
        update.message.reply_text("ဆုတောင်း မရှိသေးပါ။")
        return
    lines = []
    for r in rows:
        lines.append(f"{r['username']}: {r['text']} ({r['created_at']})")
    update.message.reply_text("\n\n".join(lines))

def quiz(update, context):
    q = db.get_random_quiz()
    if not q:
        update.message.reply_text("Quiz မရှိသေးပါ။")
        return
    qid = q["id"]
    question = q["question"]
    a = q["option_a"]; b = q["option_b"]; c = q["option_c"]; d = q["option_d"]
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"quiz|{qid}|A"),
         InlineKeyboardButton("B", callback_data=f"quiz|{qid}|B")],
        [InlineKeyboardButton("C", callback_data=f"quiz|{qid}|C"),
         InlineKeyboardButton("D", callback_data=f"quiz|{qid}|D")]
    ]
    text = f"*{question}*\n\nA. {a}\nB. {b}\nC. {c}\nD. {d}"
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def quiz_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data  # format: quiz|qid|choice
    parts = data.split("|")
    if len(parts) != 3:
        return
    _, qid, choice = parts
    user = query.from_user
    correct = db.check_quiz_answer(qid, choice)
    if correct:
        db.add_quiz_score(user.id, user.username or user.first_name, 1)
        query.edit_message_text(f"သင်ရွေးချယ်သည် {choice} — မှန်ပါသည်! 🎉")
    else:
        db.add_quiz_score(user.id, user.username or user.first_name, 0)
        query.edit_message_text(f"သင်ရွေးချယ်သည် {choice} — မမှန်ပါ။ ❌")

def tops(update, context):
    rows = db.get_top_scores(10)
    if not rows:
        update.message.reply_text("မည်သူ့မှ အမှတ် မရှိသေးပါ။")
        return
    lines = []
    rank = 1
    for r in rows:
        lines.append(f"{rank}. {r['username']} — {r['score']}")
        rank += 1
    update.message.reply_text("\n".join(lines))

def broadcast(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Admin should reply to a message to broadcast; if not, use text args
    if update.message.reply_to_message:
        # forward the replied message to all chats
        chats = db.get_stats()["chats"]
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM chats")
        rows = cur.fetchall()
        conn.close()
        count = 0
        for r in rows:
            try:
                context.bot.forward_message(chat_id=r["chat_id"], from_chat_id=update.message.reply_to_message.chat_id, message_id=update.message.reply_to_message.message_id)
                count += 1
            except Exception as e:
                logger.warning(f"Broadcast forward failed to {r['chat_id']}: {e}")
        update.message.reply_text(f"Broadcast ပြီးပါပြီ။ {count} ချက်သို့ ပို့ပြီးပါပြီ။")
    else:
        text = " ".join(context.args)
        if not text:
            update.message.reply_text("အသုံး: reply to a message and use /broadcast OR /broadcast <text>")
            return
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM chats")
        rows = cur.fetchall()
        conn.close()
        count = 0
        for r in rows:
            try:
                context.bot.send_message(chat_id=r["chat_id"], text=text)
                count += 1
            except Exception as e:
                logger.warning(f"Broadcast send failed to {r['chat_id']}: {e}")
        update.message.reply_text(f"Broadcast ပြီးပါပြီ။ {count} ချက်သို့ ပို့ပြီးပါပြီ။")

def stats(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    s = db.get_stats()
    text = f"Chats: {s['chats']}\nPrayers: {s['prayers']}\nQuizzes: {s['quizzes']}\nVerses: {s['verses']}"
    update.message.reply_text(text)

def report(update, context):
    user = update.effective_user
    text = " ".join(context.args)
    if not text:
        update.message.reply_text("အသုံး: /report <text>")
        return
    db.add_report(user.id, user.username or user.first_name, text)
    update.message.reply_text("သင့်အစီရင်ခံချက်ကို မှတ်တမ်းတင်ပြီးပါပြီ။")

def backup(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    try:
        # copy DB file
        shutil.copyfile(DB_FILE, BACKUP_FILE)
        update.message.reply_document(open(BACKUP_FILE, "rb"))
    except Exception as e:
        logger.exception(e)
        update.message.reply_text("Backup မအောင်မြင်ပါ။")

def restore(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Admin should reply to a message containing a document (the DB file)
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        update.message.reply_text("အသုံး: reply to a DB file with /restore")
        return
    doc = update.message.reply_to_message.document
    file = context.bot.getFile(doc.file_id)
    file.download(DB_FILE)
    update.message.reply_text("Restore ပြီးပါပြီ။ Bot ကို restart လုပ်ပါ။")

def allclear(update, context):
    user = update.effective_user
    if not utils.is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    db.clear_all_data()
    update.message.reply_text("Data အားလုံး ဖျက်ပြီးပါပြီ။")

def unknown(update, context):
    update.message.reply_text("မသိသော command ဖြစ်ပါသည်။ /help ကို ကြည့်ပါ။")

def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    db.init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # user commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("about", about))
    dp.add_handler(CommandHandler("verse", verse))
    dp.add_handler(CommandHandler("events", events))
    dp.add_handler(CommandHandler("birthday", birthday))
    dp.add_handler(CommandHandler("pray", pray, pass_args=True))
    dp.add_handler(CommandHandler("praylist", praylist))
    dp.add_handler(CommandHandler("quiz", quiz))
    dp.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\|"))
    dp.add_handler(CommandHandler("Tops", tops))
    dp.add_handler(CommandHandler("contact", contact))
    dp.add_handler(CommandHandler("report", report, pass_args=True))

    # admin commands
    dp.add_handler(CommandHandler("eabout", eabout, pass_args=True))
    dp.add_handler(CommandHandler("econtact", econtact, pass_args=True))
    dp.add_handler(CommandHandler("eevents", eevents, pass_args=True))
    dp.add_handler(CommandHandler("ebirthday", ebirthday, pass_args=True))
    dp.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("backup", backup))
    dp.add_handler(CommandHandler("restore", restore))
    dp.add_handler(CommandHandler("allclear", allclear))

    dp.add_handler(MessageHandler(Filters.command, unknown))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot started.")
    updater.idle()

if __name__ == "__main__":
    main()
