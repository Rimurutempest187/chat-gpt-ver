#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Church Community Telegram Bot — Fixed and Polished (python-telegram-bot v20+)
Create by : @Enoch_777
"""

import os
import sqlite3
import logging
import tempfile
import random
from datetime import datetime
from functools import wraps
from typing import Optional

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    Chat,
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip().isdigit()]
DB_PATH = os.getenv("DB_PATH", "church_bot.db")

# Logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("church_bot")

# --- Database init ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            started_at TEXT
        );
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            title TEXT,
            added_at TEXT
        );
        CREATE TABLE IF NOT EXISTS about (
            id INTEGER PRIMARY KEY,
            content TEXT,
            edited_at TEXT
        );
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        );
        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            day INTEGER,
            month INTEGER
        );
        CREATE TABLE IF NOT EXISTS prayers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            opt_a TEXT,
            opt_b TEXT,
            opt_c TEXT,
            opt_d TEXT,
            answer TEXT
        );
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            score INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


# --- Utilities -------------------------------------------------------------
def is_admin(user_id: Optional[int]) -> bool:
    return user_id in ADMIN_IDS


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Support both message and callback_query contexts
        user = update.effective_user
        uid = user.id if user else None
        if not is_admin(uid):
            if update.callback_query:
                await update.callback_query.answer("ဤ command ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။", show_alert=True)
            elif update.message:
                await update.message.reply_text("ဤ command ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
            return
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.exception("Admin command error: %s", e)
            if update.message:
                await update.message.reply_text("Admin command အတွင်း အမှားတက်နေပါသည်။ Log ကိုစစ်ပါ။")
            return

    return wrapper


def save_user(user):
    if not user:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, started_at) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username or "", user.first_name or "", user.last_name or "", datetime.utcnow().isoformat()),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to save user")
    finally:
        conn.close()


def save_group(chat: Chat):
    if not chat:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO groups (group_id, title, added_at) VALUES (?, ?, ?)",
            (chat.id, chat.title or "", datetime.utcnow().isoformat()),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to save group")
    finally:
        conn.close()


# --- Command Handlers -----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        save_user(user)
        welcome = (
            f"မင်္ဂလာပါ <b>{user.first_name or user.username or 'အသုံးပြုသူ'}</b>!\n\n"
            "Church Community Bot သို့ ကြိုဆိုပါသည်။\n\n"
            "အသုံးပြုနိုင်သော command များအတွက် /help ကိုနှိပ်ပါ။\n\n"
            "<i>Create by : @Enoch_777</i>"
        )
        await update.message.reply_html(welcome)
    except Exception:
        logger.exception("Error in /start")
        await update.message.reply_text("Start command အတွင်း အမှားတက်နေပါသည်။")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Use reply_text with parse_mode to avoid compatibility issues
    help_text = (
        "<b>အသုံးပြုနည်း လမ်းညွှန်</b>\n\n"
        "<b>Users</b>\n"
        "/start - စတင်\n"
        "/help - လမ်းညွှန်\n"
        "/about - အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက်\n"
        "/contact - တာဝန်ခံ ဖုန်းနံပါတ်များ\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက် (Random)\n"
        "/events - လာမည့် အစီအစဉ်များ\n"
        "/birthday - မွေးနေ့စာရင်း\n"
        "/pray <text> - ဆုတောင်းပေးရန်\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - Random quiz (A/B/C/D)\n"
        "/Tops - Quiz leaderboard\n"
        "/report <text> - အကြောင်းအရာ တင်ပြရန်\n\n"
        "<b>Admins</b>\n"
        "/edabout - About edit\n"
        "/edcontact - Contacts edit\n"
        "/edverse - Add verses\n"
        "/edevents - Events edit\n"
        "/edbirthday - Birthdays edit\n"
        "/edquiz - Add quizzes\n"
        "/broadcast - Broadcast to groups (reply to message or /broadcast text)\n"
        "/stats - Users/Groups count\n"
        "/backup - Send DB file\n"
        "/restore - Reply with DB file then /restore\n"
        "/allclear - Reset all data\n\n"
        "<i>Create by : @Enoch_777</i>"
    )
    # reply_text with parse_mode is more robust across versions
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


# About
@admin_only
async def edabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("About စာသားကို command နောက်တွင် ထည့်ပါ သို့မဟုတ် message ကို reply လုပ်ပါ။")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM about")
    cur.execute("INSERT INTO about (content, edited_at) VALUES (?, ?)", (text, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text("About ကို အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။")


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT content FROM about ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row and row[0].strip():
        await update.message.reply_text(row[0])
    else:
        await update.message.reply_text("About မရှိသေးပါ။ Admin ကို ဆက်သွယ်ပါ။")


# Contacts
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM contacts")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Contact မရှိသေးပါ။")
        return
    lines = [f"• <b>{r[0]}</b> — {r[1]}" for r in rows]
    await update.message.reply_text("<b>တာဝန်ခံများ</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


@admin_only
async def edcontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("Contact များကို တစ်ကြောင်းစီ 'Name - Phone' အဖြစ် ထည့်ပါ။")
        return
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM contacts")
    for ln in lines:
        if "-" in ln:
            name, phone = ln.split("-", 1)
            cur.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name.strip(), phone.strip()))
    conn.commit()
    conn.close()
    await update.message.reply_text("Contacts ထည့်ပြီးပါပြီ။")


# Verses
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT text FROM verses")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Verse မရှိသေးပါ။ Admin ကို ဆက်သွယ်ပါ။")
        return
    v = random.choice(rows)[0]
    await update.message.reply_text(v)


@admin_only
async def edverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("Verses များကို တစ်ကြောင်းစီ ထည့်ပါ။")
        return
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ln in lines:
        cur.execute("INSERT INTO verses (text) VALUES (?)", (ln,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Verses ထည့်ပြီးပါပြီ။")


# Events
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT text FROM events")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Events မရှိသေးပါ။")
        return
    text = "<b>လာမည့် အစီအစဉ်များ</b>\n\n" + "\n\n".join([r[0] for r in rows])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@admin_only
async def edevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("Events များကို တစ်ကြောင်းစီ ထည့်ပါ။")
        return
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM events")
    for ln in lines:
        cur.execute("INSERT INTO events (text) VALUES (?)", (ln,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Events ပြင်ဆင်ပြီးပါပြီ။")


# Birthdays
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, day, month FROM birthdays ORDER BY month, day")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Birthday မရှိသေးပါ။")
        return
    lines = [f"• <b>{r[0]}</b> — {r[1]}/{r[2]}" for r in rows]
    await update.message.reply_text("<b>မွေးနေ့စာရင်း</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


@admin_only
async def edbirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("Birthday များကို တစ်ကြောင်းစီ 'Name - DD/MM' အဖြစ် ထည့်ပါ။")
        return
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM birthdays")
    for ln in lines:
        if "-" in ln:
            name, date = ln.split("-", 1)
            date = date.strip().replace(" ", "/")
            try:
                d, m = date.split("/")[:2]
                cur.execute("INSERT INTO birthdays (name, day, month) VALUES (?, ?, ?)", (name.strip(), int(d), int(m)))
            except Exception:
                continue
    conn.commit()
    conn.close()
    await update.message.reply_text("Birthdays ထည့်ပြီးပါပြီ။")


# Prayers
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.partition(" ")[2].strip() if update.message and update.message.text else ""
    if not text:
        await update.message.reply_text("ဆုတောင်းလိုသော အချက်ကို command နောက်တွင် ထည့်ပါ။")
        return
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prayers (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
        (user.id, user.username or "", text, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    await update.message.reply_text("သင့်ဆုတောင်းကို မှတ်သားပြီးပါပြီ။")


async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username, text, created_at FROM prayers ORDER BY id DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    lines = [f"• @{r[0]}: {r[1]}" for r in rows]
    await update.message.reply_text("ဆုတောင်းများ\n\n" + "\n".join(lines))


# Quiz
@admin_only
async def edquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message:
        text = update.message.text.partition(" ")[2].strip()
        if not text and update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text.strip()
    if not text:
        await update.message.reply_text("Quiz များကို တစ်ကြောင်းစီ 'Question | A | B | C | D | Answer' အဖြစ် ထည့်ပါ။")
        return
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ln in lines:
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 6:
            q, a, b, c_opt, d, ans = parts[:6]
            cur.execute(
                "INSERT INTO quizzes (question, opt_a, opt_b, opt_c, opt_d, answer) VALUES (?, ?, ?, ?, ?, ?)",
                (q, a, b, c_opt, d, ans.upper()),
            )
    conn.commit()
    conn.close()
    await update.message.reply_text("Quiz များ ထည့်ပြီးပါပြီ။")


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, question, opt_a, opt_b, opt_c, opt_d FROM quizzes")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Quiz မရှိသေးပါ။ Admin ကို ဆက်သွယ်ပါ။")
        return
    q = random.choice(rows)
    qid, question, a, b, c_opt, d = q
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"quiz|{qid}|A"), InlineKeyboardButton("B", callback_data=f"quiz|{qid}|B")],
        [InlineKeyboardButton("C", callback_data=f"quiz|{qid}|C"), InlineKeyboardButton("D", callback_data=f"quiz|{qid}|D")],
    ]
    await update.message.reply_text(f"<b>Quiz</b>\n\n{question}\n\nA. {a}\nB. {b}\nC. {c_opt}\nD. {d}", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data
    try:
        _, qid, choice = data.split("|")
    except Exception:
        await query.edit_message_text("Invalid quiz data.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT answer FROM quizzes WHERE id = ?", (int(qid),))
    row = cur.fetchone()
    if not row:
        conn.close()
        await query.edit_message_text("မေးခွန်းကို ရှာမတွေ့ပါ။")
        return
    correct = row[0].upper()
    user = query.from_user
    cur.execute("SELECT id, score FROM quiz_scores WHERE user_id = ?", (user.id,))
    r = cur.fetchone()
    if r:
        sid, score = r
    else:
        cur.execute("INSERT INTO quiz_scores (user_id, username, score) VALUES (?, ?, ?)", (user.id, user.username or "", 0))
        conn.commit()
        sid = cur.lastrowid
        score = 0
    if choice.upper() == correct:
        score += 1
        cur.execute("UPDATE quiz_scores SET score = ? WHERE id = ?", (score, sid))
        conn.commit()
        await query.edit_message_text(f"မှန်ပါတယ် ✅\nယခုအမှတ်: {score}")
    else:
        await query.edit_message_text(f"မှားပါသည် ❌\nမှန်သောဖြေ: {correct}")
    conn.close()


async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username, score FROM quiz_scores ORDER BY score DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("အမှတ်စာရင်း မရှိသေးပါ။")
        return
    lines = [f"• @{r[0]} — {r[1]}" for r in rows]
    await update.message.reply_text("<b>Quiz Leaderboard</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


# Broadcast / Stats / Report / Backup / Restore / Allclear
@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT group_id FROM groups")
    groups = [r[0] for r in cur.fetchall()]
    conn.close()
    if not groups:
        await update.message.reply_text("ပို့ရန် Group မရှိသေးပါ။")
        return

    sent = 0
    if msg.reply_to_message:
        target = msg.reply_to_message
        for gid in groups:
            try:
                if target.photo:
                    await context.bot.send_chat_action(gid, ChatAction.UPLOAD_PHOTO)
                    await context.bot.send_photo(chat_id=gid, photo=target.photo[-1].file_id, caption=target.caption or "")
                elif target.text:
                    await context.bot.send_message(chat_id=gid, text=target.text)
                else:
                    await context.bot.forward_message(chat_id=gid, from_chat_id=target.chat_id, message_id=target.message_id)
                sent += 1
            except Exception as e:
                logger.warning(f"Broadcast failed to {gid}: {e}")
        await update.message.reply_text(f"Broadcast ပြီးပါပြီ။ ပို့ခဲ့သည့် Group အရေအတွက်: {sent}")
    else:
        text = msg.text.partition(" ")[2].strip()
        if not text:
            await update.message.reply_text("Broadcast အတွက် စာသားထည့်ပါ သို့မဟုတ် ပို့လိုသည့် message ကို reply လုပ်ပါ။")
            return
        for gid in groups:
            try:
                await context.bot.send_message(chat_id=gid, text=text)
                sent += 1
            except Exception as e:
                logger.warning(f"Broadcast failed to {gid}: {e}")
        await update.message.reply_text(f"Broadcast ပြီးပါပြီ။ ပို့ခဲ့သည့် Group အရေအတွက်: {sent}")


@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM groups")
    groups_count = cur.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"Users: {users_count}\nGroups: {groups_count}")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.partition(" ")[2].strip() if update.message and update.message.text else ""
    if not text:
        await update.message.reply_text("တင်ပြလိုသော အကြောင်းအရာကို ထည့်ပါ။")
        return
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, username, text, created_at) VALUES (?, ?, ?, ?)", (user.id, user.username or "", text, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text("သင့် report ကို မှတ်သားပြီးပါပြီ။ Admin များသို့ အကြောင်းကြားပေးပါမည်။")


@admin_only
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DB_PATH):
        await update.message.reply_text("Database မတွေ့ပါ။")
        return
    await update.message.reply_document(document=InputFile(DB_PATH), filename=os.path.basename(DB_PATH))
    await update.message.reply_text("Backup ဖိုင် ပေးပို့ပြီးပါပြီ။")


@admin_only
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Restore လုပ်ရန် DB ဖိုင်ကို message reply ဖြင့် ပေးပို့ပါ။")
        return
    doc = update.message.reply_to_message.document
    f = await doc.get_file()
    tmp = tempfile.NamedTemporaryFile(delete=False)
    await f.download_to_drive(tmp.name)
    tmp.close()
    try:
        os.replace(tmp.name, DB_PATH)
        await update.message.reply_text("Restore အောင်မြင်ပါသည်။")
    except Exception as e:
        await update.message.reply_text(f"Restore မအောင်မြင်ပါ: {e}")


@admin_only
async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    except Exception as e:
        logger.warning(f"Failed to remove DB: {e}")
    init_db()
    await update.message.reply_text("Database အားလုံး ဖျက်ပြီး အသစ်စတင်ထားပါပြီ။")


# Generic listener to capture groups and users
async def message_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        if chat and chat.type in ("group", "supergroup"):
            save_group(chat)
        if update.effective_user and chat and chat.type == "private":
            save_user(update.effective_user)
    except Exception:
        logger.exception("Error in message_listener")


# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Exception while handling an update: %s", context.error)


# --- Main -----------------------------------------------------------------
def main():
    init_db()
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in .env")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("birthday", birthday))
    app.add_handler(CommandHandler("pray", pray))
    app.add_handler(CommandHandler("praylist", praylist))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("Tops", tops))
    app.add_handler(CommandHandler("report", report))

    # Admin commands
    app.add_handler(CommandHandler("edabout", edabout))
    app.add_handler(CommandHandler("edcontact", edcontact))
    app.add_handler(CommandHandler("edverse", edverse))
    app.add_handler(CommandHandler("edevents", edevents))
    app.add_handler(CommandHandler("edbirthday", edbirthday))
    app.add_handler(CommandHandler("edquiz", edquiz))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("allclear", allclear))

    # Callbacks and listeners
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\|"))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), message_listener))

    app.add_error_handler(error_handler)

    logger.info("Bot started")
    app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
