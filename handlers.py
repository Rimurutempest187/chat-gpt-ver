# handlers.py
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from db import get_conn
from utils import admin_only
import config
from datetime import datetime
import random

# Helper: register user
def register_user(user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user.id, user.username or "", user.first_name or "", user.last_name or ""))
    conn.commit()
    conn.close()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    text = (
        f"မင်္ဂလာပါ {user.first_name or user.username or 'Friend'}!\n\n"
        "Church Community Bot သို့ ကြိုဆိုပါတယ်။\n\n"
        "Commands:\n"
        "/help - အသုံးပြုနည်း\n"
        "/about - အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက်\n"
        "/verse - ယနေ့ဖတ်ရန် ကျမ်းချက် (Random)\n"
        "/events - လာမည့် အစီအစဉ်များ\n"
        "/birthday - ယခုလ မွေးနေ့များ\n"
        "/pray - ဆုတောင်းပို့ရန် (သင့်ဆုတောင်းကို)\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - Random Quiz\n"
        "/report - အကြောင်းအရာ တင်ပြရန်\n\n"
        "Create by : @Enoch_777"
    )
    await update.message.reply_text(text)

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Bot အသုံးပြုနည်း လမ်းညွှန်\n\n"
        "- Admin commands: /edabout, /edcontact, /edverse, /edevents, /edbirthday, /edquiz, /broadcast, /stats, /backup, /restore, /allclear\n"
        "- Users: /start, /help, /about, /contact, /verse, /events, /birthday, /pray, /praylist, /quiz, /tops, /report\n\n"
        "Bulk insert: admin-only commands (/edverse, /edquiz) မှာ entries များကို တစ်ကြိမ်တည်းထည့်ရန် delimiter ကို အသုံးပြုပါ။\n"
        f"Delimiter: {config.BULK_DELIM}\n"
    )
    await update.message.reply_text(text)

# /about (user)
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='about'")
    row = cur.fetchone()
    conn.close()
    if row:
        await update.message.reply_text(row["value"])
    else:
        await update.message.reply_text("အသင်းတော် သမိုင်းနှင့် ရည်ရွယ်ချက် မရှိသေးပါ။ (Admin သို့ /edabout ဖြင့် ထည့်ပါ)")

# /edabout (admin)
@admin_only
async def edabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "သင့်ရဲ့ အသင်းတော် သမိုင်း/ရည်ရွယ်ချက်ကို ဒီ command နဲ့ reply message အဖြစ် ပို့ပါ။"
    if context.args:
        new = " ".join(context.args)
    else:
        # if reply
        if update.message.reply_to_message and update.message.reply_to_message.text:
            new = update.message.reply_to_message.text
        else:
            await update.message.reply_text(text)
            return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('about', ?)", (new,))
    conn.commit()
    conn.close()
    await update.message.reply_text("About ကို update ပြီးပါပြီ။")

# /contact (user)
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='contact'")
    row = cur.fetchone()
    conn.close()
    if row:
        await update.message.reply_text(row["value"])
    else:
        await update.message.reply_text("Contact မရှိသေးပါ။ (Admin သို့ /edcontact ဖြင့် ထည့်ပါ)")

# /edcontact (admin)
@admin_only
async def edcontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        new = " ".join(context.args)
    else:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            new = update.message.reply_to_message.text
        else:
            await update.message.reply_text("Contact list ထည့်ရန် message ကို reply လုပ်၍ ပို့ပါ။")
            return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('contact', ?)", (new,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Contact ကို update ပြီးပါပြီ။")

# /verse (user) random
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM verses")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Verse မရှိသေးပါ။ (Admin သို့ /edverse ဖြင့် ထည့်ပါ)")
        return
    v = random.choice(rows)
    await update.message.reply_text(v["text"])

# /edverse (admin) bulk insert
@admin_only
async def edverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Accept either reply text or args
    if context.args:
        payload = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        payload = update.message.reply_to_message.text
    else:
        await update.message.reply_text(f"Verses များကို တစ်ကြိမ်တည်းထည့်ရန် delimiter `{config.BULK_DELIM}` ဖြင့် message ကို reply လုပ်၍ ပို့ပါ။")
        return
    parts = [p.strip() for p in payload.split(config.BULK_DELIM) if p.strip()]
    conn = get_conn()
    cur = conn.cursor()
    for p in parts:
        cur.execute("INSERT INTO verses (text) VALUES (?)", (p,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"{len(parts)} verse(s) ထည့်ပြီးပါပြီ။")

# /events (user)
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY datetime")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("မရှိသေးပါ။ (Admin သို့ /edevents ဖြင့် ထည့်ပါ)")
        return
    text = "လာမည့် အစီအစဉ်များ:\n\n"
    for r in rows:
        text += f"- {r['title']} | {r['datetime']} | {r['location'] or '-'}\n"
    await update.message.reply_text(text)

# /edevents (admin)
@admin_only
async def edevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect format: Title ||| datetime ||| location ||| note
    if context.args:
        payload = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        payload = update.message.reply_to_message.text
    else:
        await update.message.reply_text(f"Event ထည့်ရန် format: Title{config.BULK_DELIM}datetime{config.BULK_DELIM}location (multiple events separated by {config.BULK_DELIM})")
        return
    parts = [p.strip() for p in payload.split(config.BULK_DELIM) if p.strip()]
    conn = get_conn()
    cur = conn.cursor()
    # If single event with fields separated by '|||' then insert one
    if len(parts) >= 2 and ("|" in parts[0] or len(parts) == 4):
        # try parse as single event fields
        if len(parts) >= 2:
            title = parts[0]
            dt = parts[1]
            loc = parts[2] if len(parts) >=3 else ""
            note = parts[3] if len(parts) >=4 else ""
            cur.execute("INSERT INTO events (title, datetime, location, note) VALUES (?, ?, ?, ?)", (title, dt, loc, note))
            conn.commit()
            conn.close()
            await update.message.reply_text("Event ထည့်ပြီးပါပြီ။")
            return
    # Otherwise treat each part as a simple event text
    for p in parts:
        cur.execute("INSERT INTO events (title, datetime, location, note) VALUES (?, ?, ?, ?)", (p, "", "", ""))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"{len(parts)} event(s) ထည့်ပြီးပါပြီ။")

# /birthday (user)
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM birthdays ORDER BY month, day")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Birthday list မရှိသေးပါ။ (Admin သို့ /edbirthday ဖြင့် ထည့်ပါ)")
        return
    text = "ယခုလ မွေးနေ့များ:\n\n"
    now_month = datetime.now().month
    for r in rows:
        if r["month"] == now_month:
            text += f"- {r['name']} ({r['day']}/{r['month']}) {r['note'] or ''}\n"
    if text.strip() == "ယခုလ မွေးနေ့များ:\n\n":
        text = "ယခုလ မွေးနေ့ရှိသူ မရှိသေးပါ။"
    await update.message.reply_text(text)

# /edbirthday (admin) bulk insert: format name|day|month|note per line separated by BULK_DELIM
@admin_only
async def edbirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        payload = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        payload = update.message.reply_to_message.text
    else:
        await update.message.reply_text(f"Birthday များကို တစ်ကြိမ်တည်းထည့်ရန် delimiter `{config.BULK_DELIM}` ဖြင့် message ကို reply လုပ်၍ ပို့ပါ။ Format per entry: name|day|month|note")
        return
    entries = [e.strip() for e in payload.split(config.BULK_DELIM) if e.strip()]
    conn = get_conn()
    cur = conn.cursor()
    count = 0
    for e in entries:
        parts = [p.strip() for p in e.split("|")]
        if len(parts) >= 3:
            name = parts[0]
            day = int(parts[1])
            month = int(parts[2])
            note = parts[3] if len(parts) >=4 else ""
            cur.execute("INSERT INTO birthdays (name, day, month, note) VALUES (?, ?, ?, ?)", (name, day, month, note))
            count += 1
    conn.commit()
    conn.close()
    await update.message.reply_text(f"{count} birthday(s) ထည့်ပြီးပါပြီ။")

# /pray (user)
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("ဆုတောင်းကို message reply ဖြင့် ပို့ပါ (သို့) /pray <text>")
        return
    text = " ".join(context.args) if context.args else update.message.reply_to_message.text
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO prayers (user_id, username, text) VALUES (?, ?, ?)", (user.id, user.username or "", text))
    conn.commit()
    conn.close()
    await update.message.reply_text("သင့်ဆုတောင်းကို မှတ်သားပြီးပါပြီ။")

# /praylist (user)
async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prayers ORDER BY created_at DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    text = "ဆုတောင်းများ (နောက်ဆုံး 50):\n\n"
    for r in rows:
        text += f"- @{r['username'] or 'anonymous'}: {r['text']}\n"
    await update.message.reply_text(text)

# /quiz (user) random quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quizzes")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Quiz မရှိသေးပါ။ (Admin သို့ /edquiz ဖြင့် ထည့်ပါ)")
        return
    q = random.choice(rows)
    text = f"{q['question']}\nA. {q['choice_a']}\nB. {q['choice_b']}\nC. {q['choice_c']}\nD. {q['choice_d']}\n\nReply with A/B/C/D to answer."
    # store current quiz in user_data for checking
    context.user_data["current_quiz"] = {"id": q["id"], "answer": q["answer"].upper()}
    await update.message.reply_text(text)

# handle quiz answer (simple)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().upper()
    if txt in ("A","B","C","D") and context.user_data.get("current_quiz"):
        q = context.user_data.pop("current_quiz")
        correct = q["answer"].upper()
        user = update.effective_user
        if txt == correct:
            # increment score
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM quiz_scores WHERE user_id=?", (user.id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE quiz_scores SET score = score + 1 WHERE user_id=?", (user.id,))
            else:
                cur.execute("INSERT INTO quiz_scores (user_id, username, score) VALUES (?, ?, ?)", (user.id, user.username or "", 1))
            conn.commit()
            conn.close()
            await update.message.reply_text("မှန်ပါတယ်! +1 point")
        else:
            await update.message.reply_text(f"မမှန်ပါ။ မှန်答案: {correct}")
        return
    # fallback: ignore or treat as report
    await update.message.reply_text("Command မသိပါ။ /help ကို ကြည့်ပါ။")

# /edquiz (admin) bulk insert
@admin_only
async def edquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect each quiz entry separated by BULK_DELIM, each entry fields separated by newline or '|'
    if context.args:
        payload = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        payload = update.message.reply_to_message.text
    else:
        await update.message.reply_text(f"Quiz များကို တစ်ကြိမ်တည်းထည့်ရန် delimiter `{config.BULK_DELIM}` ဖြင့် message ကို reply လုပ်၍ ပို့ပါ။ Format per entry: question|A|B|C|D|answer_letter")
        return
    entries = [e.strip() for e in payload.split(config.BULK_DELIM) if e.strip()]
    conn = get_conn()
    cur = conn.cursor()
    count = 0
    for e in entries:
        # try split by | or newline
        parts = [p.strip() for p in e.replace("\n","|").split("|")]
        if len(parts) >= 6:
            q, a, b, c, d, ans = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            ans = ans.strip().upper()[0]
            if ans not in ("A","B","C","D"):
                continue
            cur.execute("INSERT INTO quizzes (question, choice_a, choice_b, choice_c, choice_d, answer) VALUES (?, ?, ?, ?, ?, ?)",
                        (q, a, b, c, d, ans))
            count += 1
    conn.commit()
    conn.close()
    await update.message.reply_text(f"{count} quiz(es) ထည့်ပြီးပါပြီ။")

# /tops (quiz leaderboard)
async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, score FROM quiz_scores ORDER BY score DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("Leaderboard မရှိသေးပါ။")
        return
    text = "Quiz Top Scores:\n\n"
    rank = 1
    for r in rows:
        text += f"{rank}. @{r['username'] or 'anonymous'} — {r['score']}\n"
        rank += 1
    await update.message.reply_text(text)

# /broadcast (admin) - send text or photo to all groups and users
@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If reply to a message, broadcast that message (text or photo)
    bot = context.bot
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM groups")
    groups = [r["id"] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users")
    users = [r["id"] for r in cur.fetchall()]
    conn.close()
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        # if photo
        if msg.photo:
            file_id = msg.photo[-1].file_id
            for gid in groups:
                try:
                    await bot.send_photo(chat_id=gid, photo=file_id, caption=msg.caption or "")
                except Exception:
                    pass
            for uid in users:
                try:
                    await bot.send_photo(chat_id=uid, photo=file_id, caption=msg.caption or "")
                except Exception:
                    pass
            await update.message.reply_text("Broadcast (photo) ပို့ပြီးပါပြီ။")
            return
        else:
            text = msg.text or msg.caption or ""
    else:
        # use args as text
        if context.args:
            text = " ".join(context.args)
        else:
            await update.message.reply_text("Broadcast ပို့ရန် message ကို reply လုပ်၍ ပို့ပါ (သို့) /broadcast <text>")
            return
    for gid in groups:
        try:
            await bot.send_message(chat_id=gid, text=text)
        except Exception:
            pass
    for uid in users:
        try:
            await bot.send_message(chat_id=uid, text=text)
        except Exception:
            pass
    await update.message.reply_text("Broadcast ပို့ပြီးပါပြီ။")

# /stats (admin)
@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    users = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM groups")
    groups = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM verses")
    verses = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM quizzes")
    quizzes = cur.fetchone()["c"]
    conn.close()
    text = f"Stats:\nUsers: {users}\nGroups: {groups}\nVerses: {verses}\nQuizzes: {quizzes}"
    await update.message.reply_text(text)

# /report (user)
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if context.args:
        text = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    else:
        await update.message.reply_text("Report ပို့ရန် /report <text> သို့မဟုတ် message ကို reply လုပ်၍ ပို့ပါ။")
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, username, text) VALUES (?, ?, ?)", (user.id, user.username or "", text))
    conn.commit()
    conn.close()
    await update.message.reply_text("Report ကို မှတ်သားပြီးပါပြီ။")

# /backup (admin)
@admin_only
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from db import backup_db
    import time
    ts = int(time.time())
    path = f"backups/backup_{ts}.sql"
    Path("backups").mkdir(parents=True, exist_ok=True)
    backup_db(path)
    await update.message.reply_text(f"Backup created: {path}")

# /restore (admin) - expects reply to a message containing dump text or file path (simple)
@admin_only
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from db import restore_db_from_dump
    if update.message.reply_to_message and update.message.reply_to_message.document:
        # download file
        doc = update.message.reply_to_message.document
        f = await doc.get_file()
        local = f"backups/{doc.file_name}"
        await f.download_to_drive(local)
        restore_db_from_dump(local)
        await update.message.reply_text("Restore ပြီးပါပြီ။")
    else:
        await update.message.reply_text("Restore လုပ်ရန် backup file ကို reply လုပ်၍ ပို့ပါ။")

# /allclear (admin)
@admin_only
async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    tables = ["verses","events","birthdays","prayers","quizzes","quiz_scores","reports","groups","users","settings"]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
    await update.message.reply_text("All data cleared.")
