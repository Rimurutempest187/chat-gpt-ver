#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Church Community Bot - ready to run (python-telegram-bot v13.15)
Author: Enoch_777 (Create by shown in bot messages)
"""
import os
import sqlite3
import logging
import shutil
import random
import datetime
from io import BytesIO
from dotenv import load_dotenv

from PIL import Image

from telegram import (
    Update,
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

# Load .env
load_dotenv()

# ---------------- Configuration (from .env) ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_BOT_TOKEN")
ADMIN_IDS = []
admin_env = os.getenv("ADMIN_IDS", "")
if admin_env:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_env.split(",") if x.strip()]
    except Exception:
        ADMIN_IDS = []
DB_FILE = os.getenv("DB_FILE", "church_bot.db")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")

os.makedirs(BACKUP_DIR, exist_ok=True)

# ---------------- Logging ----------------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Conversation states ----------------
(
    EDABOUT_TEXT,
    EDCONTACT_ADD,
    EDVERSE_WAIT,
    EDEVENTS_WAIT,
    EDBIRTHDAY_WAIT,
    EDQUIZ_FLOW_Q,
    EDQUIZ_FLOW_A,
    BROADCAST_TEXT,
    RESTORE_WAIT_FILE,
) = range(9)

# ---------------- DB helpers ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS about (id INTEGER PRIMARY KEY, content TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS verses (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, datetime TEXT, location TEXT, description TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS birthdays (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, day INTEGER, month INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS prayers (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, text TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, choice_a TEXT, choice_b TEXT, choice_c TEXT, choice_d TEXT, answer TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, score INTEGER, last_played TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, text TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, title TEXT)""")
    conn.commit()
    conn.close()

def db_execute(query, params=(), fetch=False, many=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if many:
            c.executemany(query, params)
            conn.commit()
            return None
        c.execute(query, params)
        if fetch:
            rows = c.fetchall()
            conn.commit()
            return rows
        conn.commit()
        return None
    finally:
        conn.close()

# ---------------- Utilities ----------------
def is_admin(user_id):
    return user_id in ADMIN_IDS

def format_datetime(dt_str):
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str

# ---------------- User commands (clearly separated) ----------------

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    text = (
        f"မင်္ဂလာပါ {user.first_name}!\n\n"
        "Church Community Bot သို့ ကြိုဆိုပါသည်။\n\n"
        "အသုံးပြုနိုင်သော command များအတွက် /help ကိုနှိပ်ပါ။\n\n"
        "Create by : @Enoch_777"
    )
    update.message.reply_text(text)

def help_cmd(update: Update, context: CallbackContext):
    help_text = (
        "အသုံးပြုနည်း လမ်းညွှန်\n\n"
        "/start - စတင်အသုံးပြုခြင်း\n"
        "/help - ဒီစာမျက်နှာ\n"
        "/about - အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက်\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက် (Random)\n"
        "/events - လာမည့် အစီအစဉ်များ\n"
        "/birthday - ယခုလ မွေးနေ့စာရင်း\n"
        "/contact - တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/pray <text> - ဆုတောင်းပေးစေလိုသည်များ ပေးပို့ရန်\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - Random Quiz (ABCD)\n"
        "/Tops - Quiz အမှတ် အများဆုံး\n"
        "/report <text> - သတင်း/အကြောင်းအရာ တင်ပြရန်\n\n"
        "Admin commands (only admins): /edabout, /edcontact, /edverse, /edquiz, /edevents, /edbirthday, /broadcast, /backup, /restore, /allclear, /stats"
    )
    update.message.reply_text(help_text)

def about(update: Update, context: CallbackContext):
    rows = db_execute("SELECT content FROM about WHERE id=1", fetch=True)
    if rows and rows[0][0]:
        update.message.reply_text(rows[0][0])
    else:
        update.message.reply_text("အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက် မရှိသေးပါ။ (Admin ထားပြီး /edabout ဖြင့် ထည့်ပါ)")

def contact(update: Update, context: CallbackContext):
    rows = db_execute("SELECT name, phone FROM contacts", fetch=True)
    if not rows:
        update.message.reply_text("Contact မရှိသေးပါ။")
        return
    out = "တာဝန်ခံများ ဖုန်းနံပါတ်များ:\n\n"
    for r in rows:
        out += f"{r[0]} — {r[1]}\n"
    update.message.reply_text(out)

def verse(update: Update, context: CallbackContext):
    rows = db_execute("SELECT text FROM verses", fetch=True)
    if not rows:
        update.message.reply_text("Verse မရှိသေးပါ။ Admin ကို ဆက်သွယ်ပါ။")
        return
    text = random.choice(rows)[0]
    update.message.reply_text(text)

def events(update: Update, context: CallbackContext):
    rows = db_execute("SELECT title, datetime, location, description FROM events ORDER BY datetime", fetch=True)
    if not rows:
        update.message.reply_text("လာမည့် အစီအစဉ် မရှိသေးပါ။")
        return
    out = "လာမည့် အစီအစဉ်များ:\n\n"
    for r in rows:
        out += f"**{r[0]}**\n{format_datetime(r[1])} @ {r[2]}\n{r[3]}\n\n"
    update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

def birthday(update: Update, context: CallbackContext):
    today = datetime.date.today()
    rows = db_execute("SELECT name, day, month FROM birthdays ORDER BY month, day", fetch=True)
    if not rows:
        update.message.reply_text("Birthday စာရင်း မရှိသေးပါ။")
        return
    out = "ယခုလ မွေးနေ့များ:\n\n"
    for r in rows:
        name, day, month = r
        if month == today.month:
            out += f"{name} — {day}/{month}\n"
    if out.strip() == "ယခုလ မွေးနေ့များ:":
        out = "ယခုလ မွေးနေ့ရှိသူ မရှိသေးပါ။"
    update.message.reply_text(out)

def pray(update: Update, context: CallbackContext):
    user = update.effective_user
    text = " ".join(context.args) if context.args else None
    if not text:
        update.message.reply_text("ဆုတောင်းပေးစေလိုသော အချက်ကို /pray <text> ဖြင့် ပေးပို့ပါ။")
        return
    created_at = datetime.datetime.utcnow().isoformat()
    db_execute("INSERT INTO prayers (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
               (user.id, user.username or user.first_name, text, created_at))
    update.message.reply_text("သင့်ဆုတောင်းကို မှတ်တမ်းတင်ပြီးပါပြီ။")

def praylist(update: Update, context: CallbackContext):
    rows = db_execute("SELECT username, text, created_at FROM prayers ORDER BY id DESC", fetch=True)
    if not rows:
        update.message.reply_text("ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    out = "ဆုတောင်းစာရင်း:\n\n"
    for r in rows[:50]:
        out += f"@{r[0]}: {r[1]}\n"
    update.message.reply_text(out)

def quiz(update: Update, context: CallbackContext):
    rows = db_execute("SELECT id, question, choice_a, choice_b, choice_c, choice_d FROM quiz", fetch=True)
    if not rows:
        update.message.reply_text("Quiz မရှိသေးပါ။ Admin ကို ဆက်သွယ်ပါ။")
        return
    q = random.choice(rows)
    qid = q[0]
    question = q[1]
    choices = [q[2], q[3], q[4], q[5]]
    context.user_data['current_quiz'] = qid
    keyboard = [
        [InlineKeyboardButton("A", callback_data="quiz_A"), InlineKeyboardButton("B", callback_data="quiz_B")],
        [InlineKeyboardButton("C", callback_data="quiz_C"), InlineKeyboardButton("D", callback_data="quiz_D")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"{question}\n\nA. {choices[0]}\nB. {choices[1]}\nC. {choices[2]}\nD. {choices[3]}", reply_markup=reply_markup)

def tops(update: Update, context: CallbackContext):
    rows = db_execute("SELECT username, score FROM quiz_scores ORDER BY score DESC LIMIT 10", fetch=True)
    if not rows:
        update.message.reply_text("အမှတ်စာရင်း မရှိသေးပါ။")
        return
    out = "Quiz Top Scores:\n\n"
    for i, r in enumerate(rows, start=1):
        out += f"{i}. @{r[0]} — {r[1]}\n"
    update.message.reply_text(out)

def report_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    text = " ".join(context.args) if context.args else None
    if not text:
        update.message.reply_text("တင်ပြလိုသည့် အကြောင်းအရာကို /report <text> ဖြင့် ပေးပို့ပါ။")
        return
    created_at = datetime.datetime.utcnow().isoformat()
    db_execute("INSERT INTO reports (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
               (user.id, user.username or user.first_name, text, created_at))
    update.message.reply_text("သင့်တင်ပြချက်ကို မှတ်တမ်းတင်ပြီးပါပြီ။ Admin များသို့ အကြောင်းကြားပေးပါမည်။")

# Inline callback for quiz answers
def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    data = query.data
    query.answer()
    if data.startswith("quiz_"):
        choice = data.split("_")[1]
        qid = context.user_data.get('current_quiz')
        if not qid:
            query.edit_message_text("မေးခွန်းတစ်ခု မရွေးထားပါ။ /quiz ဖြင့် စတင်ပါ။")
            return
        rows = db_execute("SELECT answer FROM quiz WHERE id=?", (qid,), fetch=True)
        if not rows:
            query.edit_message_text("မေးခွန်းကို ရှာမတွေ့ပါ။")
            return
        correct = (rows[0][0] or "").strip().upper()
        if choice == correct:
            prev = db_execute("SELECT score FROM quiz_scores WHERE user_id=?", (user.id,), fetch=True)
            if prev and len(prev) and prev[0][0] is not None:
                new_score = prev[0][0] + 1
                db_execute("UPDATE quiz_scores SET score=?, last_played=? WHERE user_id=?", (new_score, datetime.datetime.utcnow().isoformat(), user.id))
            else:
                new_score = 1
                db_execute("INSERT INTO quiz_scores (user_id, username, score, last_played) VALUES (?, ?, ?, ?)",
                           (user.id, user.username or user.first_name, new_score, datetime.datetime.utcnow().isoformat()))
            query.edit_message_text(f"မှန်ပါသည်! သင်ရရှိသော အမှတ်: {new_score}")
        else:
            query.edit_message_text(f"မှားပါသည်။ မှန်ကန်သော ဖြေ: {correct}")

# ---------------- Admin commands (clearly separated) ----------------

def edabout_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက်ကို ရေးထည့်ပါ။ (တစ်ကြောင်းလုံးပို့ပါ OR multiline ပို့၍တစ်ချက်တည်းထည့်လို့ရသည်) /cancel ဖြင့် ပယ်ဖျက်နိုင်သည်။")
    return EDABOUT_TEXT

def edabout_save(update: Update, context: CallbackContext):
    text = update.message.text
    db_execute("INSERT OR REPLACE INTO about (id, content) VALUES (1, ?)", (text,))
    update.message.reply_text("About ကို သိမ်းဆည်းပြီးပါပြီ။")
    return ConversationHandler.END

def edcontact_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("အသစ်ထည့်မည့် Contact များကို 'Name - Phone' အဖြင့် တစ်ကြောင်းစီပို့ပါ။\nBulk ထည့်ရန် multiple lines သို့မဟုတ် CSV (line-per-contact) ပို့ပါ။")
    return EDCONTACT_ADD

def edcontact_add(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    # Support bulk (multiple lines)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    inserted = 0
    for line in lines:
        if "-" in line:
            name, phone = [s.strip() for s in line.split("-", 1)]
            db_execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
            inserted += 1
    update.message.reply_text(f"{inserted} contact(s) ထည့်ပြီးပါပြီ။")
    return ConversationHandler.END

# edverse: support bulk multiline OR interactive
def edverse_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("Verses တွေကို တစ်ကြောင်းချင်းစီ new line ဖြင့် ပို့ပါ (bulk)၊ သို့မဟုတ် တစ်ကြောင်းတည်းတင်ပြီး /done များကို အသုံးပြုနိုင်ပါသည်။")
    context.user_data['edverse_buffer'] = []
    return EDVERSE_WAIT

def edverse_add(update: Update, context: CallbackContext):
    text = update.message.text
    # If multiline -> treat as bulk
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) > 1:
        # replace all verses with these lines
        db_execute("DELETE FROM verses")
        db_execute("INSERT INTO verses (text) VALUES (?)", [(l,) for l in lines], many=True)
        update.message.reply_text(f"{len(lines)} verse(s) ထည့်ပြီးပါပြီ။")
        return ConversationHandler.END
    else:
        # single line -> add to buffer and wait for /done or more
        context.user_data.setdefault('edverse_buffer', []).append(text.strip())
        update.message.reply_text("ထည့်ပြီး — နောက်တစ်ကြောင်းထည့်ပါ သို့မဟုတ် /done ဖြင့် ပြီးစီးပါ။")
        return EDVERSE_WAIT

def edverse_done(update: Update, context: CallbackContext):
    buffer = context.user_data.pop('edverse_buffer', [])
    if buffer:
        db_execute("DELETE FROM verses")
        db_execute("INSERT INTO verses (text) VALUES (?)", [(b,) for b in buffer], many=True)
        update.message.reply_text(f"{len(buffer)} verse(s) ထည့်ပြီးပါပြီ။")
    else:
        update.message.reply_text("Verse မရှိပါ။")
    return ConversationHandler.END

def edverse_bulk_command(update: Update, context: CallbackContext):
    # Alternative: admin can call /edverse_bulk with the multiline in same message
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    text = update.message.text.partition(' ')[2]  # get rest after command
    if not text.strip():
        update.message.reply_text("Usage: /edverse_bulk <paste multiple verses each on new line>")
        return
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    db_execute("DELETE FROM verses")
    db_execute("INSERT INTO verses (text) VALUES (?)", [(l,) for l in lines], many=True)
    update.message.reply_text(f"{len(lines)} verse(s) ထည့်ပြီးပါပြီ။")

# edevents
def edevents_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("Event များကို တစ်ကြောင်းစီ 'Title | YYYY-MM-DD HH:MM | Location | Description' အဖြင့် ပေးပို့ပါ။ (bulk သုံးရန် multiline အသုံးပြုပါ။)")
    context.user_data['edevents_buffer'] = []
    return EDEVENTS_WAIT

def edevents_add(update: Update, context: CallbackContext):
    text = update.message.text
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    inserted = 0
    for line in lines:
        if '|' in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                title, dt, loc, desc = parts[0], parts[1], parts[2], parts[3]
                db_execute("INSERT INTO events (title, datetime, location, description) VALUES (?, ?, ?, ?)",
                           (title, dt, loc, desc))
                inserted += 1
    update.message.reply_text(f"{inserted} event(s) ထည့်ပြီးပါပြီ။")
    return ConversationHandler.END

def edbirthday_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("Birthday ကို 'Name - DD-MM' ပုံစံဖြင့် တစ်ကြောင်းစီပို့ပါ (bulk permitted via multiline).")
    context.user_data['edbirthday_buffer'] = []
    return EDBIRTHDAY_WAIT

def edbirthday_add(update: Update, context: CallbackContext):
    text = update.message.text
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    inserted = 0
    for line in lines:
        if "-" in line:
            name, dm = [s.strip() for s in line.split("-", 1)]
            try:
                day, month = [int(x) for x in dm.split("-")]
            except Exception:
                continue
            db_execute("INSERT INTO birthdays (name, day, month) VALUES (?, ?, ?)", (name, day, month))
            inserted += 1
    update.message.reply_text(f"{inserted} birthday(s) ထည့်ပြီးပါပြီ။")
    return ConversationHandler.END

# edquiz: interactive flow or bulk (single message with multiple quiz lines)
def edquiz_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text(
        "Quiz ထည့်ရန် —\n"
        "1) Bulk: တစ်ကြောင်း = Question | A | B | C | D | AnswerLetter (e.g. A/B/C/D)\n"
        "   Example line: What is 2+2? | 1 | 2 | 3 | 4 | D\n"
        "   Bulk အားလုံးကို multiline ဖြင့် paste လုပ်ပါ။\n\n"
        "2) Or interactive: တစ်ခုပြီးတစ်ခု ထည့်ချင်ရင် စတင်မလား? (Yes/No not implemented — use interactive by calling /edquiz_flow)\n"
    )
    return EDQUIZ_FLOW_Q

def edquiz_bulk(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    # Get text after command if any
    raw = update.message.text.partition(' ')[2] or ""
    # If user simply replies with multiline without rest after command, use entire message text
    if not raw.strip():
        raw = update.message.text
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    inserted = 0
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6:
            q, a, b, c, d, ans = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            ans = ans.strip().upper()
            if ans not in ("A", "B", "C", "D"):
                continue
            db_execute("INSERT INTO quiz (question, choice_a, choice_b, choice_c, choice_d, answer) VALUES (?, ?, ?, ?, ?, ?)",
                       (q, a, b, c, d, ans))
            inserted += 1
    update.message.reply_text(f"{inserted} quiz(s) ထည့်ပြီးပါပြီ။")

# broadcast
def broadcast_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("Broadcast ပို့ရန် message သို့မဟုတ် ပုံတစ်ပုံ upload ပြီး caption ထည့်ပါ။")
    return BROADCAST_TEXT

def broadcast_send(update: Update, context: CallbackContext):
    msg = update.message
    chats = db_execute("SELECT chat_id FROM chats", fetch=True)
    if not chats:
        update.message.reply_text("Broadcast ပို့ရန် chat မရှိသေးပါ။ Bot ကို group/chat တွင် add လုပ်ပါ။")
        return ConversationHandler.END
    chat_ids = [c[0] for c in chats]
    sent = 0
    failed = 0
    if msg.photo:
        photo = msg.photo[-1]
        file_id = photo.file_id
        caption = msg.caption or ""
        for cid in chat_ids:
            try:
                context.bot.send_photo(chat_id=cid, photo=file_id, caption=caption)
                sent += 1
            except Exception as e:
                logger.warning("Broadcast photo failed to %s: %s", cid, e)
                failed += 1
    else:
        text = msg.text or ""
        for cid in chat_ids:
            try:
                context.bot.send_message(chat_id=cid, text=text)
                sent += 1
            except Exception as e:
                logger.warning("Broadcast text failed to %s: %s", cid, e)
                failed += 1
    update.message.reply_text(f"Broadcast ပြီးစီးပါသည်။ Sent: {sent}, Failed: {failed}")
    return ConversationHandler.END

def stats_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    users_count = db_execute("SELECT COUNT(DISTINCT user_id) FROM prayers", fetch=True)
    chats_count = db_execute("SELECT COUNT(*) FROM chats", fetch=True)
    quiz_count = db_execute("SELECT COUNT(*) FROM quiz", fetch=True)
    users = users_count[0][0] if users_count else 0
    chats = chats_count[0][0] if chats_count else 0
    qcount = quiz_count[0][0] if quiz_count else 0
    update.message.reply_text(f"Stats:\nUsers (prayer reporters): {users}\nChats stored: {chats}\nQuiz count: {qcount}")

def backup_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_name = f"backup_{ts}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    try:
        shutil.copyfile(DB_FILE, backup_path)
        with open(backup_path, "rb") as f:
            update.message.reply_document(document=f, filename=backup_name)
    except Exception as e:
        logger.exception("Backup failed")
        update.message.reply_text("Backup မအောင်မြင်ပါ။")

def restore_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    update.message.reply_text("Restore လုပ်ရန် DB ဖိုင်ကို Document အဖြစ် upload ပြီး /restore_confirm ဖြင့် အတည်ပြုပါ။")
    return RESTORE_WAIT_FILE

def restore_confirm(update: Update, context: CallbackContext):
    msg = update.message
    if not msg.document:
        update.message.reply_text("Document မရှိပါ။ DB ဖိုင်ကို upload ပြီး /restore_confirm ဖြင့် ပြန်ခေါ်ပါ။")
        return ConversationHandler.END
    file = msg.document.get_file()
    tmp_path = os.path.join(BACKUP_DIR, "restore_tmp.db")
    file.download(tmp_path)
    try:
        shutil.copyfile(tmp_path, DB_FILE)
        update.message.reply_text("Restore ပြီးစီးပါပြီ။ Bot ကို restart လိုအပ်နိုင်သည်။")
    except Exception as e:
        logger.exception("Restore failed")
        update.message.reply_text("Restore မအောင်မြင်ပါ။")
    return ConversationHandler.END

def allclear_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("Admin မဟုတ်ပါ။")
        return
    db_execute("DELETE FROM about")
    db_execute("DELETE FROM contacts")
    db_execute("DELETE FROM verses")
    db_execute("DELETE FROM events")
    db_execute("DELETE FROM birthdays")
    db_execute("DELETE FROM prayers")
    db_execute("DELETE FROM quiz")
    db_execute("DELETE FROM quiz_scores")
    db_execute("DELETE FROM reports")
    db_execute("DELETE FROM chats")
    update.message.reply_text("Database အားလုံး ဖျက်ပြီးပါပြီ။")

# ---------------- Misc handlers ----------------
def new_chat_member_handler(update: Update, context: CallbackContext):
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup"):
        try:
            db_execute("INSERT OR REPLACE INTO chats (chat_id, title) VALUES (?, ?)", (chat.id, chat.title))
        except Exception:
            pass

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("မသိသော command ဖြစ်ပါသည်။ /help ကို ကြည့်ပါ။")

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# ---------------- Conversation handlers setup ----------------
def build_conversation_handlers(dispatcher):
    # edabout conv
    conv_edabout = ConversationHandler(
        entry_points=[CommandHandler("edabout", edabout_start)],
        states={EDABOUT_TEXT: [MessageHandler(Filters.text & ~Filters.command, edabout_save)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_edabout)

    # edcontact
    conv_edcontact = ConversationHandler(
        entry_points=[CommandHandler("edcontact", edcontact_start)],
        states={EDCONTACT_ADD: [MessageHandler(Filters.text & ~Filters.command, edcontact_add)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_edcontact)

    # edverse
    conv_edverse = ConversationHandler(
        entry_points=[CommandHandler("edverse", edverse_start)],
        states={EDVERSE_WAIT: [MessageHandler(Filters.text & ~Filters.command, edverse_add)]},
        fallbacks=[
            CommandHandler("done", edverse_done),
            CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1]),
        ],
    )
    dispatcher.add_handler(conv_edverse)
    # edverse bulk command
    dispatcher.add_handler(CommandHandler("edverse_bulk", edverse_bulk_command))

    # edevents
    conv_edevents = ConversationHandler(
        entry_points=[CommandHandler("edevents", edevents_start)],
        states={EDEVENTS_WAIT: [MessageHandler(Filters.text & ~Filters.command, edevents_add)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_edevents)

    # edbirthday
    conv_edbirthday = ConversationHandler(
        entry_points=[CommandHandler("edbirthday", edbirthday_start)],
        states={EDBIRTHDAY_WAIT: [MessageHandler(Filters.text & ~Filters.command, edbirthday_add)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_edbirthday)

    # edquiz - bulk via /edquiz_bulk or interactive via /edquiz (interactive not fully implemented beyond explanation)
    dispatcher.add_handler(CommandHandler("edquiz_bulk", edquiz_bulk))
    dispatcher.add_handler(CommandHandler("edquiz", edquiz_start))

    # broadcast conv
    conv_broadcast = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={BROADCAST_TEXT: [MessageHandler(Filters.text | Filters.photo, broadcast_send)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_broadcast)

    # restore conv
    conv_restore = ConversationHandler(
        entry_points=[CommandHandler("restore", restore_start)],
        states={RESTORE_WAIT_FILE: [MessageHandler(Filters.document, restore_confirm)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: (u.message.reply_text("Cancelled."), ConversationHandler.END)[1])],
    )
    dispatcher.add_handler(conv_restore)

# ---------------- Main ----------------
def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Set command list for Telegram UI
    try:
        updater.bot.set_my_commands([
            BotCommand("start", "Start"),
            BotCommand("help", "Help"),
            BotCommand("about", "About the church"),
            BotCommand("verse", "Random verse"),
            BotCommand("events", "Upcoming events"),
            BotCommand("birthday", "Birthdays this month"),
            BotCommand("contact", "Contacts"),
            BotCommand("quiz", "Play quiz"),
            BotCommand("Tops", "Quiz top scores"),
        ])
    except Exception:
        pass

    # User commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("about", about))
    dp.add_handler(CommandHandler("contact", contact))
    dp.add_handler(CommandHandler("verse", verse))
    dp.add_handler(CommandHandler("events", events))
    dp.add_handler(CommandHandler("birthday", birthday))
    dp.add_handler(CommandHandler("pray", pray))
    dp.add_handler(CommandHandler("praylist", praylist))
    dp.add_handler(CommandHandler("quiz", quiz))
    dp.add_handler(CommandHandler("Tops", tops))
    dp.add_handler(CommandHandler("report", report_cmd))

    # Admin commands
    dp.add_handler(CommandHandler("edabout", edabout_start))
    dp.add_handler(CommandHandler("edcontact", edcontact_start))
    dp.add_handler(CommandHandler("edverse", edverse_start))
    dp.add_handler(CommandHandler("edverse_bulk", edverse_bulk_command))
    dp.add_handler(CommandHandler("edevents", edevents_start))
    dp.add_handler(CommandHandler("edbirthday", edbirthday_start))
    dp.add_handler(CommandHandler("edquiz", edquiz_start))
    dp.add_handler(CommandHandler("edquiz_bulk", edquiz_bulk))
    dp.add_handler(CommandHandler("broadcast", broadcast_start))
    dp.add_handler(CommandHandler("backup", backup_cmd))
    dp.add_handler(CommandHandler("restore", restore_start))
    dp.add_handler(CommandHandler("allclear", allclear_cmd))
    dp.add_handler(CommandHandler("stats", stats_cmd))

    # Callback query for quiz
    dp.add_handler(CallbackQueryHandler(callback_query_handler))

    # Group tracking
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_member_handler))
    dp.add_handler(MessageHandler(Filters.text & Filters.group, new_chat_member_handler))

    # Build conversation handlers (edverse, broadcast, restore, etc.)
    build_conversation_handlers(dp)

    # Unknown
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # Error handler
    dp.add_error_handler(error_handler)

    # Start polling
    updater.start_polling()
    logger.info("Bot started.")
    updater.idle()

if __name__ == "__main__":
    main()
