## File: `handlers.py`

import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db import get_db
from utils import is_admin, format_event, format_contact
from datetime import datetime

DB = None

async def init(db_path):
    global DB
    DB = get_db(db_path)
    await DB.init()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"မင်္ဂလာပါ {user.first_name or ''}!\n\n"
        "Church Community Bot မှ ကြိုဆိုပါသည်။\n\n"
        "အသုံးပြုရန် /help ကို အသုံးပြုပါ။\n\n"
        "Create by : @Enoch_777"
    )
    await update.message.reply_text(text)
    # register user
    await DB.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, joined_at) VALUES (?,?,?,?,?)",
        (user.id, user.username or '', user.first_name or '', user.last_name or '', datetime.utcnow().isoformat()),
    )

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "/start — စတင်အသုံးပြုရန်\n"
        "/help — ညွှန်ကြားချက်များ\n"
        "/about — အသင်းအကြောင်း\n"
        "/contact — တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/verse — ယနေ့ဖတ်ရန်ကျမ်းချက်\n"
        "/events — လာမည့်အစီအစဉ်များ\n"
        "/birthday — ယခုလ မွေးနေ့များ\n"
        "/pray <text> — စာရင်းထည့်ရန်\n"
        "/praylist — ဆုတောင်းစာရင်းများ\n"
        "/quiz — ကွစ်ဇ်ကစားရန်\n"
        "/Tops — ကွစ်ဇ် အကောင်းဆုံးများ\n"
        "/report <text> — အကြောင်းအရာတင်ပြရန်\n"
    )
    await update.message.reply_text(txt)

# /eabout and /about
async def eabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only command.")
        return
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Usage: /eabout <text>")
        return
    await DB.execute("INSERT OR REPLACE INTO settings (key,value) VALUES ('about',?)", (text,))
    await update.message.reply_text("About text updated.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = await DB.fetchone("SELECT value FROM settings WHERE key='about'")
    await update.message.reply_text(row['value'] if row else "(မသတ်မှတ်ထားသေးပါ)")

# /contact /econtact
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT * FROM contacts ORDER BY id")
    if not rows:
        await update.message.reply_text("No contacts set.")
        return
    text = '\n'.join([format_contact(r) for r in rows])
    await update.message.reply_text(text)

async def econtact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only command.")
        return
    # expect: /econtact Name|Phone
    payload = ' '.join(context.args)
    if '|' not in payload:
        await update.message.reply_text("Usage: /econtact Name|Phone (use | as separator)")
        return
    name, phone = [p.strip() for p in payload.split('|',1)]
    await DB.execute("INSERT INTO contacts (name,phone) VALUES (?,?)", (name, phone))
    await update.message.reply_text("Contact added.")

# /verse (daily verse)
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.utcnow().date().isoformat()
    row = await DB.fetchone("SELECT text FROM verses WHERE date=?", (today,))
    if row:
        await update.message.reply_text(row['text'])
    else:
        await update.message.reply_text("No verse set for today.")

# /events /eevents
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT * FROM events ORDER BY datetime")
    if not rows:
        await update.message.reply_text("No events")
        return
    text = '\n\n'.join([format_event(r) for r in rows])
    await update.message.reply_text(text)

async def eevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only command.")
        return
    payload = ' '.join(context.args)
    # expect: Title|YYYY-MM-DD HH:MM|Location|Description
    if '|' not in payload:
        await update.message.reply_text("Usage: /eevents Title|YYYY-MM-DD HH:MM|Location|Description")
        return
    title, dt, location, desc = [p.strip() for p in payload.split('|',3)]
    await DB.execute("INSERT INTO events (title,datetime,location,description) VALUES (?,?,?,?)", (title, dt, location, desc))
    await update.message.reply_text("Event added.")

# /birthday /ebirthday
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT * FROM birthdays")
    if not rows:
        await update.message.reply_text("No birthdays set.")
        return
    text = '\n'.join([f"{r['name']} — {r['day_month']}" for r in rows])
    await update.message.reply_text(text)

async def ebirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only command.")
        return
    payload = ' '.join(context.args)
    # expect: Name|MM-DD
    if '|' not in payload:
        await update.message.reply_text("Usage: /ebirthday Name|MM-DD")
        return
    name, mmdd = [p.strip() for p in payload.split('|',1)]
    await DB.execute("INSERT INTO birthdays (name,day_month) VALUES (?,?)", (name, mmdd))
    await update.message.reply_text("Birthday added.")

# /pray /praylist
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Usage: /pray <text>")
        return
    await DB.execute("INSERT INTO prayers (telegram_id,username,text,created_at) VALUES (?,?,?,?)",
                     (user.id, user.username or '', text, datetime.utcnow().isoformat()))
    await update.message.reply_text("Your prayer request has been recorded.")

async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT * FROM prayers ORDER BY id DESC")
    if not rows:
        await update.message.reply_text("No prayers recorded.")
        return
    text = '\n\n'.join([f"@{r['username']} — {r['text']}" for r in rows])
    await update.message.reply_text(text)

# /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Usage: /report <text>")
        return
    await DB.execute("INSERT INTO reports (telegram_id,username,text,created_at) VALUES (?,?,?,?)",
                     (user.id, user.username or '', text, datetime.utcnow().isoformat()))
    await update.message.reply_text("Report sent. Thank you.")

# /quiz and callbacks
from random import choice

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT * FROM quiz_questions")
    if not rows:
        await update.message.reply_text("No quiz questions available.")
        return
    q = choice(rows)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("A", callback_data=f"quiz|{q['id']}|a"),
        InlineKeyboardButton("B", callback_data=f"quiz|{q['id']}|b"),
        InlineKeyboardButton("C", callback_data=f"quiz|{q['id']}|c"),
        InlineKeyboardButton("D", callback_data=f"quiz|{q['id']}|d"),
    ]])
    txt = f"{q['question']}\nA: {q['a']}\nB: {q['b']}\nC: {q['c']}\nD: {q['d']}"
    await update.message.reply_text(txt, reply_markup=kb)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith('quiz|'):
        return
    _, qid, choice_letter = data.split('|')
    q = await DB.fetchone("SELECT * FROM quiz_questions WHERE id=?", (int(qid),))
    if not q:
        await query.edit_message_text("Question not found.")
        return
    correct = (q['answer'].lower() == choice_letter.lower())
    user = query.from_user
    if correct:
        # increment score
        row = await DB.fetchone("SELECT * FROM quiz_scores WHERE telegram_id=?", (user.id,))
        if row:
            await DB.execute("UPDATE quiz_scores SET score = score + 1 WHERE telegram_id=?", (user.id,))
        else:
            await DB.execute("INSERT INTO quiz_scores (telegram_id,username,score) VALUES (?,?,?)", (user.id, user.username or '', 1))
        await query.edit_message_text(f"✅ Correct! Answer: {q[q['answer']]} ")
    else:
        await query.edit_message_text(f"❌ Incorrect. Correct answer: {q[q['answer']]} ")

async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await DB.fetchall("SELECT username,score FROM quiz_scores ORDER BY score DESC LIMIT 10")
    if not rows:
        await update.message.reply_text("No scores yet.")
        return
    text = "\n".join([f"{i+1}. @{r['username']} — {r['score']}" for i, r in enumerate(rows)])
    await update.message.reply_text(text)

# /broadcast (admin)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only")
        return
    # two modes: reply-to-message -> forward that message to all users
    # or /broadcast Your message text -> send text to all users
    users = await DB.fetchall("SELECT telegram_id FROM users")
    if update.message.reply_to_message:
        # forward the replied message to everyone
        msg_to_forward = update.message.reply_to_message
        await update.message.reply_text(f"Sending to {len(users)} users...")
        for u in users:
            try:
                await context.bot.copy_message(chat_id=u['telegram_id'], from_chat_id=msg_to_forward.chat_id, message_id=msg_to_forward.message_id)
            except Exception:
                continue
        await update.message.reply_text("Broadcast complete.")
    else:
        text = ' '.join(context.args)
        if not text:
            await update.message.reply_text("Usage: /broadcast <text> or reply to a message and run /broadcast")
            return
        await update.message.reply_text(f"Sending to {len(users)} users...")
        for u in users:
            try:
                await context.bot.send_message(chat_id=u['telegram_id'], text=text)
            except Exception:
                continue
        await update.message.reply_text("Broadcast complete.")

# /stats (admin)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only")
        return
    total = await DB.fetchone("SELECT COUNT(*) as c FROM users")
    cnt = total['c'] if total else 0
    await update.message.reply_text(f"Total registered users: {cnt}")

# /backup /restore
async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only")
        return
    path = await DB.backup()
    await update.message.reply_text(f"Backup created: {path}")

async def restore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only")
        return
    # Expect admin to reply to a document with /restore
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Reply to the DB file (as document) with /restore to restore")
        return
    doc = update.message.reply_to_message.document
    fpath = f"data/{doc.file_name}"
    await doc.get_file().download_to_drive(custom_path=fpath)
    await DB.restore_from_file(fpath)
    await update.message.reply_text("Database restored from uploaded file. Please restart the bot if necessary.")

# /allclear
async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Admin only")
        return
    await DB.clear_all()
    await update.message.reply_text("All data cleared.")

# fallback handlers for unknown commands can be added in bot.py
