from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from db import *
from utils import now_iso, format_event, footer
from config import ADMIN_IDS
import io

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "", user.first_name or "", user.last_name or "", now_iso())
    text = f"မင်္ဂလာပါ {user.first_name or user.username or 'Member'}!\n\nChurch Community Bot သို့ ကြိုဆိုပါတယ်။{footer()}"
    await update.message.reply_text(text)

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - စတင်အသုံးပြုခြင်း\n"
        "/help - လမ်းညွှန်\n"
        "/about - အသင်းအကြောင်း\n"
        "/eabout - (Admin) about edit\n"
        "/contact - တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/econtact - (Admin) edit contacts\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက်များ\n"
        "/events - လာမည့်အစီအစဉ်များ\n"
        "/eevents - (Admin) edit events\n"
        "/birthday - ယခုလ မွေးနေ့များ\n"
        "/ebirthday - (Admin) add birthday\n"
        "/pray <text> - ဆုတောင်းပေးရန်\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - ကျမ်းစာ ဉာဏ်စမ်း\n"
        "/Tops - Quiz ranking\n"
        "/broadcast - (Admin) သတင်းပို့ရန်\n"
        "/stats - (Admin) အသုံးပြုသူ အချက်အလက်\n"
        "/report <text> - သတင်းတင်ပြရန်\n"
        "/backup - DB export (Admin)\n"
        "/restore - DB import (Admin) (send file)\n"
        "/allclear - (Admin) data ဖျက်ရန်\n"
    )
    await update.message.reply_text(text)

# /about and /eabout
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = get_about()
    if content:
        await update.message.reply_text(content + footer())
    else:
        await update.message.reply_text("အသင်းအကြောင်း မရှိသေးပါ။")

# Conversation states for editing about
EABOUT = range(1)
async def eabout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("သင်သည် admin မဟုတ်ပါ။")
        return ConversationHandler.END
    await update.message.reply_text("အသင်းအကြောင်းကို အသစ်ထည့်ပါ။")
    return 0

async def eabout_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    set_about(text)
    await update.message.reply_text("Updated.")
    return ConversationHandler.END

# /contact and /econtact
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list_contacts()
    if not rows:
        await update.message.reply_text("Contact မရှိသေးပါ။")
        return
    text = "Contacts:\n" + "\n".join([f"{r['name']} - {r['phone']}" for r in rows])
    await update.message.reply_text(text)

ECONTACT = range(1)
async def econtact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("သင်သည် admin မဟုတ်ပါ။")
        return ConversationHandler.END
    await update.message.reply_text("Add contact as: Name - Phone")
    return 0

async def econtact_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "-" not in text:
        await update.message.reply_text("Format: Name - Phone")
        return ConversationHandler.END
    name, phone = [s.strip() for s in text.split("-", 1)]
    add_contact(name, phone)
    await update.message.reply_text("Contact added.")
    return ConversationHandler.END

# /verse
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import date
    today = date.today().isoformat()
    rows = get_today_verses(today)
    if not rows:
        await update.message.reply_text("ယနေ့အတွက် verse မရှိသေးပါ။")
        return
    text = "\n\n".join([r["verse"] for r in rows])
    await update.message.reply_text(text)

# /events and /eevents
async def events_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list_events()
    if not rows:
        await update.message.reply_text("မည်သည့် event မရှိသေးပါ။")
        return
    text = "\n\n".join([format_event(r) for r in rows])
    await update.message.reply_text(text, parse_mode="Markdown")

EEVENTS = range(1)
async def eevents_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("သင်သည် admin မဟုတ်ပါ။")
        return ConversationHandler.END
    await update.message.reply_text("Add event as: Title | YYYY-MM-DD HH:MM | Location | Description")
    return 0

async def eevents_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 4:
        await update.message.reply_text("Format မှားနေပါသည်။")
        return ConversationHandler.END
    title, dt, loc, desc = parts[:4]
    add_event(title, dt, loc, desc)
    await update.message.reply_text("Event added.")
    return ConversationHandler.END

# /birthday and /ebirthday
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import date
    m = date.today().month
    rows = birthdays_this_month(m)
    if not rows:
        await update.message.reply_text("ယခုလတွင် မွေးနေ့ မရှိသေးပါ။")
        return
    text = "\n".join([f"{r['name']} - {r['day']}/{r['month']} {r['note'] or ''}" for r in rows])
    await update.message.reply_text(text)

EBIRTHDAY = range(1)
async def ebirthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("သင်သည် admin မဟုတ်ပါ။")
        return ConversationHandler.END
    await update.message.reply_text("Add birthday as: Name - DD - MM - Note(optional)")
    return 0

async def ebirthday_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = [p.strip() for p in text.split("-")]
    if len(parts) < 3:
        await update.message.reply_text("Format မှားနေပါသည်။")
        return ConversationHandler.END
    name = parts[0]
    day = int(parts[1])
    month = int(parts[2])
    note = parts[3] if len(parts) > 3 else ""
    add_birthday(name, day, month, note)
    await update.message.reply_text("Birthday added.")
    return ConversationHandler.END

# /pray and /praylist
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = " ".join(context.args) if context.args else (update.message.text or "")
    if not text:
        await update.message.reply_text("ဆုတောင်းလိုသော အချက်ကို ရိုက်ထည့်ပါ။ /pray <text>")
        return
    add_prayer(user.id, user.username or user.first_name, text, now_iso())
    await update.message.reply_text("သင့်ဆုတောင်းကို မှတ်တမ်းတင်ပြီးပါပြီ။")

async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list_prayers()
    if not rows:
        await update.message.reply_text("ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    text = "\n\n".join([f"{r['username'] or r['user_id']}: {r['text']}" for r in rows])
    await update.message.reply_text(text)

# /quiz and quiz flow (simple)
async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = get_random_quiz()
    if not q:
        await update.message.reply_text("Quiz မရှိသေးပါ။ Admin သို့မဟုတ် /eevents ကဲ့သို့ admin tools ဖြင့် ထည့်ပါ။")
        return
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"quiz|{q['id']}|A"),
         InlineKeyboardButton("B", callback_data=f"quiz|{q['id']}|B")],
        [InlineKeyboardButton("C", callback_data=f"quiz|{q['id']}|C"),
         InlineKeyboardButton("D", callback_data=f"quiz|{q['id']}|D")]
    ]
    text = f"{q['question']}\nA. {q['choice_a']}\nB. {q['choice_b']}\nC. {q['choice_c']}\nD. {q['choice_d']}"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

from telegram.ext import CallbackQueryHandler

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # format quiz|id|choice
    try:
        _, qid, choice = data.split("|")
    except:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quiz WHERE id = ?", (qid,))
    q = cur.fetchone()
    conn.close()
    if not q:
        await query.edit_message_text("Question not found.")
        return
    correct = q["answer"].upper()
    user = query.from_user
    if choice.upper() == correct:
        update_score(user.id, user.username or user.first_name, 1)
        await query.edit_message_text("Correct! +1 point")
    else:
        await query.edit_message_text(f"Wrong. Correct answer: {correct}")

# /Tops
async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = top_scores(10)
    if not rows:
        await update.message.reply_text("No scores yet.")
        return
    text = "Top Scores:\n" + "\n".join([f"{i+1}. {r['username']} - {r['score']}" for i, r in enumerate(rows)])
    await update.message.reply_text(text)

# /broadcast (admin)
BROADCAST_WAIT = range(1)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return ConversationHandler.END
    await update.message.reply_text("Send the message to broadcast. You may attach a photo. Text only or photo + caption.")
    return 0

async def broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return ConversationHandler.END
    # collect all users
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    rows = cur.fetchall()
    conn.close()
    user_ids = [r["id"] for r in rows]
    # message content
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
        caption = update.message.caption or ""
        for uid in user_ids:
            try:
                await context.bot.send_photo(chat_id=uid, photo=bio, caption=caption)
                bio.seek(0)
            except Exception:
                continue
    else:
        text = update.message.text or ""
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
            except Exception:
                continue
    await update.message.reply_text("Broadcast sent.")
    return ConversationHandler.END

# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    users_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM prayers")
    prayers_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM reports")
    reports_count = cur.fetchone()["c"]
    conn.close()
    text = f"Users: {users_count}\nPrayers: {prayers_count}\nReports: {reports_count}"
    await update.message.reply_text(text)

# /report
async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = " ".join(context.args) if context.args else (update.message.text or "")
    if not text:
        await update.message.reply_text("Report text ထည့်ပါ။ /report <text>")
        return
    add_report(user.id, user.username or user.first_name, text, now_iso())
    await update.message.reply_text("Report received. Thank you.")

# /backup and /restore and /allclear
async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    data = export_db_bytes()
    await update.message.reply_document(document=io.BytesIO(data), filename="church_backup.db")
    await update.message.reply_text("Backup sent.")

async def restore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not update.message.document:
        await update.message.reply_text("Please send the DB file as a document.")
        return
    doc = update.message.document
    bio = io.BytesIO()
    await doc.get_file().download_to_memory(out=bio)
    bio.seek(0)
    import_db_bytes(bio.read())
    await update.message.reply_text("Database restored. Restart bot to apply changes.")

async def allclear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    clear_all_data()
    await update.message.reply_text("All data cleared.")

# fallback / unknown
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. /help ကိုကြည့်ပါ။")
