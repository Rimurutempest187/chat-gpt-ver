# bot.py
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from utils import BOT_TOKEN, is_admin, ADMIN_IDS
import db
from datetime import datetime
import tempfile

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize DB
db.init_db()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    db.save_chat({
        "id": chat.id,
        "type": chat.type,
        "username": chat.username,
        "title": chat.title,
        "first_name": chat.first_name,
        "last_name": chat.last_name
    })
    text = "မင်္ဂလာပါ။ Church Community Bot သို့ ကြိုဆိုပါတယ်။\n\n" \
           "အသုံးပြုရန် /help ကိုနှိပ်ပါ။\n\n" \
           "Create by : @Enoch_777"
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/start - စတင်အသုံးပြုခြင်း\n"
        "/help - လမ်းညွှန်\n"
        "/about - အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက်\n"
        "/contact - တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက် (Random)\n"
        "/events - လာမည့်အစီအစဉ်များ\n"
        "/birthday - ယခုလ မွေးနေ့များ\n"
        "/pray - ဆုတောင်းပေးစေလိုသည့်အချက် (ပို့ရန်: /pray <text>)\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - Random Quiz\n"
        "/Tops - Quiz အမှတ် အများဆုံး\n"
        "/report - သတင်း/အကြောင်းအရာ တင်ပြရန် (ပို့ရန်: /report <text>)\n"
        "Admin commands: /edabout /edcontact /edverse /edevents /edbirthday /edquiz /broadcast /stats /backup /restore /allclear\n"
    )
    await update.message.reply_text(help_text)

# about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = db.get_about()
    if not text:
        text = "အသင်းတော်/လူငယ်အဖွဲ့ အကြောင်း မရှိသေးပါ။"
    await update.message.reply_text(text)

async def edabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Expect the rest of message as content
    args = context.args
    if not args:
        await update.message.reply_text("အသင်းအကြောင်းကို ထည့်ရန် /edabout <text>")
        return
    text = " ".join(args)
    db.set_about(text)
    await update.message.reply_text("About ကို ပြင်ဆင်ပြီးပါပြီ။")

# contacts
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_contacts()
    if not rows:
        await update.message.reply_text("တာဝန်ခံ ဖုန်းနံပါတ် မရှိသေးပါ။")
        return
    text = "တာဝန်ခံများ\n"
    for r in rows:
        text += f"- {r['name']}: {r['phone']}\n"
    await update.message.reply_text(text)

async def edcontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Expect format: name - phone ; multiple lines or separated by '---'
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text("အသုံး: /edcontact Name - Phone (သို့) အများများထည့်ရန် '---' ဖြင့်ခွဲပါ")
        return
    # clear existing and add new
    db.clear_contacts()
    entries = raw.split('---')
    for e in entries:
        if '-' in e:
            name, phone = e.split('-', 1)
            db.add_contact(name.strip(), phone.strip())
    await update.message.reply_text("Contacts ပြင်ဆင်ပြီးပါပြီ။")

# verses
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    v = db.random_verse()
    if not v:
        await update.message.reply_text("Verse မရှိသေးပါ။ Admin ကို /edverse ဖြင့် ထည့်ရန်။")
        return
    await update.message.reply_text(v)

async def edverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text("အသုံး: /edverse verse1 --- verse2 --- verse3")
        return
    entries = [e.strip() for e in raw.split('---') if e.strip()]
    if entries:
        db.add_verses_bulk(entries)
        await update.message.reply_text(f"{len(entries)} verses ထည့်ပြီးပါပြီ။")
    else:
        await update.message.reply_text("မထည့်နိုင်ပါ။ ဖော်ပြချက်ကို စစ်ဆေးပါ။")

# events
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_events()
    if not rows:
        await update.message.reply_text("လာမည့် အစီအစဉ် မရှိသေးပါ။")
        return
    text = "Upcoming Events:\n"
    for r in rows:
        text += f"- {r['title']} | {r['datetime']} | {r['location']} {(' - '+r['note']) if r['note'] else ''}\n"
    await update.message.reply_text(text)

async def edevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text("အသုံး: /edevents Title | YYYY-MM-DD HH:MM | Location | Note (သို့) အများများ '---' ဖြင့်ခွဲပါ")
        return
    entries = [e.strip() for e in raw.split('---') if e.strip()]
    db.clear_events()
    for e in entries:
        parts = [p.strip() for p in e.split('|')]
        title = parts[0] if len(parts) > 0 else ""
        datetime_str = parts[1] if len(parts) > 1 else ""
        location = parts[2] if len(parts) > 2 else ""
        note = parts[3] if len(parts) > 3 else ""
        db.add_event(title, datetime_str, location, note)
    await update.message.reply_text(f"{len(entries)} events ထည့်ပြီးပါပြီ။")

# birthdays
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    month = now.month
    rows = db.birthdays_in_month(month)
    if not rows:
        await update.message.reply_text("ယခုလ မွေးနေ့ရှိသူ မရှိသေးပါ။")
        return
    text = f"ယခုလ ({month}) မွေးနေ့များ\n"
    for r in rows:
        text += f"- {r['name']} : {r['day']}\n"
    await update.message.reply_text(text)

async def edbirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text("အသုံး: /edbirthday Name - DD/MM (သို့) အများများ '---' ဖြင့်ခွဲပါ")
        return
    db.clear_birthdays()
    entries = [e.strip() for e in raw.split('---') if e.strip()]
    for e in entries:
        if '-' in e:
            name, dm = e.split('-', 1)
            dm = dm.strip()
            if '/' in dm:
                day, month = dm.split('/', 1)
                try:
                    db.add_birthday(name.strip(), int(day), int(month))
                except:
                    continue
    await update.message.reply_text(f"{len(entries)} birthdays ထည့်ပြီးပါပြီ။")

# prayers
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text("အသုံး: /pray <ဆုတောင်းလိုသည့်အချက်>")
        return
    text = " ".join(args)
    db.add_prayer(user.id, user.username or user.full_name, text)
    await update.message.reply_text("သင့်ဆုတောင်းကို မှတ်တမ်းတင်ပြီးပါပြီ။")

async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_prayers()
    if not rows:
        await update.message.reply_text("ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    text = "ဆုတောင်းများ\n"
    for r in rows:
        text += f"- @{r['username'] if r['username'] else r['user_id']}: {r['text']}\n"
    await update.message.reply_text(text)

# quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = db.random_quiz()
    if not row:
        await update.message.reply_text("Quiz မရှိသေးပါ။ Admin ကို /edquiz ဖြင့် ထည့်ပါ။")
        return
    qid = row["id"]
    question = row["question"]
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"quiz|{qid}|A"),
         InlineKeyboardButton("B", callback_data=f"quiz|{qid}|B")],
        [InlineKeyboardButton("C", callback_data=f"quiz|{qid}|C"),
         InlineKeyboardButton("D", callback_data=f"quiz|{qid}|D")]
    ]
    text = f"{question}\n\nA. {row['opt_a']}\nB. {row['opt_b']}\nC. {row['opt_c']}\nD. {row['opt_d']}"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # format: quiz|qid|choice
    parts = data.split("|")
    if len(parts) != 3:
        return
    _, qid_str, choice = parts
    qid = int(qid_str)
    correct = db.get_quiz_answer(qid)
    user = query.from_user
    if correct and choice.upper() == correct.upper():
        db.increment_score(user.id, user.username or user.full_name, 1)
        await query.edit_message_text(f"မှန်ပါတယ် ✅\nသင်ရွေးချယ်သည်: {choice}")
    else:
        await query.edit_message_text(f"မှားပါသည် ❌\nသင်ရွေးချယ်သည်: {choice}\nမှန်答案: {correct}")

# edquiz
async def edquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text("အသုံး: /edquiz Q|A|B|C|D|Answer (သို့) အများများ '---' ဖြင့်ခွဲပါ")
        return
    entries = [e.strip() for e in raw.split('---') if e.strip()]
    questions = []
    for e in entries:
        parts = [p.strip() for p in e.split('|')]
        if len(parts) >= 6:
            q, a, b, c, d, ans = parts[:6]
            questions.append((q, a, b, c, d, ans.upper()))
    if questions:
        db.add_quiz_bulk(questions)
        await update.message.reply_text(f"{len(questions)} quiz များ ထည့်ပြီးပါပြီ။")
    else:
        await update.message.reply_text("မထည့်နိုင်ပါ။ ဖော်ပြချက်ကို စစ်ဆေးပါ။")

# Tops
async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.top_scores(10)
    if not rows:
        await update.message.reply_text("အမှတ်စာရင်း မရှိသေးပါ။")
        return
    text = "Quiz Top Scores\n"
    rank = 1
    for r in rows:
        text += f"{rank}. {r['username'] or 'Unknown'} — {r['score']}\n"
        rank += 1
    await update.message.reply_text(text)

# broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Usage: /broadcast <text> (attach photo optionally)
    text = " ".join(context.args)
    if not text and not update.message.photo:
        await update.message.reply_text("အသုံး: /broadcast <message> (သို့) ပုံနှင့်ပို့နိုင်သည်။")
        return
    # gather all chats
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM chats")
    rows = cur.fetchall()
    conn.close()
    count = 0
    for r in rows:
        chat_id = r["chat_id"]
        try:
            if update.message.photo:
                # send photo with caption
                photo = update.message.photo[-1]
                await context.bot.send_photo(chat_id=chat_id, photo=photo.file_id, caption=text)
            else:
                await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except Exception as e:
            logger.warning(f"Broadcast failed to {chat_id}: {e}")
    await update.message.reply_text(f"Broadcast ပို့ပြီးပါပြီ။ ပို့သွားသော စာရင်း: {count}")

# stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    s = db.get_stats()
    await update.message.reply_text(f"Users: {s['users']}\nGroups: {s['groups']}")

# report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text("အသုံး: /report <text>")
        return
    text = " ".join(args)
    db.add_report(user.id, user.username or user.full_name, text)
    await update.message.reply_text("သင့် report ကို မှတ်တမ်းတင်ပြီးပါပြီ။")

# backup
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    db.backup_db(tmp.name)
    await update.message.reply_document(open(tmp.name, "rb"), filename="church_bot_backup.db")
    os.unlink(tmp.name)

# restore
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Expect a file attachment
    if not update.message.document:
        await update.message.reply_text("အသုံး: /restore (attach database file)")
        return
    doc = update.message.document
    file = await doc.get_file()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    await file.download_to_drive(tmp.name)
    tmp.close()
    try:
        db.restore_db(tmp.name)
        await update.message.reply_text("Database ကို ပြန်လည်ထည့်သွင်းပြီးပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"Restore မအောင်မြင်ပါ: {e}")
    finally:
        os.unlink(tmp.name)

# allclear
async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Danger: clear all tables
    db.clear_contacts()
    db.clear_events()
    db.clear_verses()
    db.clear_birthdays()
    db.clear_prayers()
    db.clear_quiz()
    db.reset_scores()
    await update.message.reply_text("Database အချက်အလက်များအားလုံး ဖျက်ပြီးပါပြီ။")

# message handler to save chats
async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    db.save_chat({
        "id": chat.id,
        "type": chat.type,
        "username": chat.username,
        "title": chat.title,
        "first_name": chat.first_name,
        "last_name": chat.last_name
    })

# register handlers
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN မရှိပါ။ config.env ထဲတွင် ထည့်ပါ။")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("edabout", edabout))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("edcontact", edcontact))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("edverse", edverse))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("edevents", edevents))
    app.add_handler(CommandHandler("birthday", birthday))
    app.add_handler(CommandHandler("edbirthday", edbirthday))
    app.add_handler(CommandHandler("pray", pray))
    app.add_handler(CommandHandler("praylist", praylist))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\|"))
    app.add_handler(CommandHandler("edquiz", edquiz))
    app.add_handler(CommandHandler("Tops", tops))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("allclear", allclear))

    # catch-all to save chat info
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), any_message))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
