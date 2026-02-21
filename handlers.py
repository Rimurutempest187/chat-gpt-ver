# handlers.py
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import db, utils
from datetime import datetime
import io

# States for conversations
BROADCAST_WAIT = 1
RESTORE_WAIT = 2
QUIZ_ANSWER = 3
EDABOUT_WAIT = 4
EDCONTACT_WAIT = 5
EDVERSE_WAIT = 6
EDEVENTS_WAIT = 7
EDBIRTHDAY_WAIT = 8
EDQUIZ_WAIT = 9
PRAY_WAIT = 10
REPORT_WAIT = 11

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.execute(
        "INSERT OR REPLACE INTO users(user_id, username, first_name, last_name, is_bot, joined_at) VALUES(?,?,?,?,?,?)",
        (user.id, user.username or "", user.first_name or "", user.last_name or "", int(user.is_bot), utils.now_iso())
    )
    text = (
        f"မင်္ဂလာပါ {user.first_name or ''}!\n\n"
        "Church Community Bot သို့ ကြိုဆိုပါတယ်။\n\n"
        "Commands:\n"
        "/help - အသုံးပြုနည်း\n"
        "/about - အသင်းအကြောင်း\n"
        "/verse - ယနေ့ဖတ်ရန်ကျမ်းချက်\n"
        "/events - လာမည့်အစီအစဉ်များ\n"
        "/quiz - စမ်းသပ်မေးခွန်း\n\n"
        "Create by : @Enoch_777"
    )
    await update.message.reply_text(text)

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "အသုံးပြုနည်း - Commands\n"
        "/start - စတင်\n"
        "/help - ဒီစာမျက်နှာ\n"
        "/about - အသင်းအကြောင်း\n"
        "/verse - Random verse\n"
        "/events - Upcoming events\n"
        "/birthday - ဒီလ မွေးနေ့များ\n"
        "/pray - ဆုတောင်းပေးရန် (/pray <text>)\n"
        "/praylist - ဆုတောင်းစာရင်း\n"
        "/quiz - Random quiz\n"
        "/tops - Quiz အမှတ်အများဆုံး\n"
        "/report - အကြောင်းအရာတင်ပြရန် (/report <text>)\n\n"
        "Admin commands:\n"
        "/edabout - edit about\n"
        "/edcontact - edit contacts\n"
        "/edverse - add verses (bulk allowed)\n"
        "/edevents - edit events\n"
        "/edbirthday - add birthdays\n"
        "/edquiz - add quizzes (bulk allowed)\n"
        "/broadcast - send message to all groups/users\n"
        "/stats - show counts\n"
        "/backup - get DB backup\n"
        "/restore - restore DB (upload file)\n"
        "/allclear - delete all data\n"
    )
    await update.message.reply_text(text)

# /about and /edabout
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = await db.fetchone("SELECT text FROM about")
    if row and row[0]:
        await update.message.reply_text(row[0])
    else:
        await update.message.reply_text("အသင်းအကြောင်း မရှိသေးပါ။ (Admin များ /edabout ဖြင့် ထည့်ပါ)")

async def edabout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return ConversationHandler.END
    await update.message.reply_text("အသင်းအကြောင်းကို ရေးထည့်ပါ (send message).")
    return EDBOUT_WAIT if False else EDBOUT_WAIT  # placeholder

# Simpler: single message handler for edabout
async def edabout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    text = update.message.text_html or update.message.text
    await db.execute("DELETE FROM about")
    await db.execute("INSERT INTO about(text) VALUES(?)", (text,))
    await update.message.reply_text("Updated about.")

# /contact and /edcontact
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT name, phone FROM contacts")
    if not rows:
        await update.message.reply_text("Contact list is empty.")
        return
    text = "\n".join([f"{r[0]} - {r[1]}" for r in rows])
    await update.message.reply_text(text)

async def edcontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # Expect lines like: Name - Phone
    lines = utils.parse_bulk_lines(update.message.text)
    # If first token is /edcontact, remove it
    if lines and lines[0].startswith("/edcontact"):
        lines = lines[1:]
    await db.execute("DELETE FROM contacts")
    for line in lines:
        if "-" in line:
            name, phone = [p.strip() for p in line.split("-", 1)]
            await db.execute("INSERT OR REPLACE INTO contacts(name, phone) VALUES(?,?)", (name, phone))
    await update.message.reply_text("Contacts updated.")

# /verse and /edverse
import random
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT text FROM verses")
    if not rows:
        await update.message.reply_text("No verses available.")
        return
    text = random.choice(rows)[0]
    await update.message.reply_text(text)

async def edverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # Accept bulk: each line is a verse
    lines = utils.parse_bulk_lines(update.message.text)
    # Remove command line if present
    if lines and lines[0].startswith("/edverse"):
        lines = lines[1:]
    for line in lines:
        await db.execute("INSERT INTO verses(text) VALUES(?)", (line,))
    await update.message.reply_text(f"Added {len(lines)} verses.")

# /events and /edevents
async def events_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT id, text FROM events ORDER BY id")
    if not rows:
        await update.message.reply_text("No events.")
        return
    text = "\n\n".join([f"{r[0]}. {r[1]}" for r in rows])
    await update.message.reply_text(text)

async def edevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    lines = utils.parse_bulk_lines(update.message.text)
    if lines and lines[0].startswith("/edevents"):
        lines = lines[1:]
    await db.execute("DELETE FROM events")
    for line in lines:
        await db.execute("INSERT INTO events(text) VALUES(?)", (line,))
    await update.message.reply_text(f"Events updated ({len(lines)}).")

# /birthday and /edbirthday
async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT name, month, day FROM birthdays ORDER BY month, day")
    if not rows:
        await update.message.reply_text("No birthdays.")
        return
    text = "\n".join([f"{r[0]} - {r[1]}/{r[2]}" for r in rows])
    await update.message.reply_text(text)

async def edbirthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # Expect lines like: Name - MM-DD or Name - M D
    lines = utils.parse_bulk_lines(update.message.text)
    if lines and lines[0].startswith("/edbirthday"):
        lines = lines[1:]
    await db.execute("DELETE FROM birthdays")
    for line in lines:
        if "-" in line:
            name, date = [p.strip() for p in line.split("-", 1)]
            if "/" in date:
                m, d = [int(x) for x in date.split("/", 1)]
            elif "-" in date:
                m, d = [int(x) for x in date.split("-", 1)]
            else:
                parts = date.split()
                m, d = int(parts[0]), int(parts[1])
            await db.execute("INSERT INTO birthdays(name, month, day) VALUES(?,?,?)", (name, m, d))
    await update.message.reply_text("Birthdays updated.")

# /pray and /praylist
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Use /pray <text> to submit a prayer request.")
        return
    await db.execute("INSERT INTO prayers(user_id, username, text, created_at) VALUES(?,?,?,?)",
                     (user.id, user.username or "", text, utils.now_iso()))
    await update.message.reply_text("Your prayer request has been recorded.")

async def praylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT username, text, created_at FROM prayers ORDER BY id DESC")
    if not rows:
        await update.message.reply_text("No prayer requests.")
        return
    text = "\n\n".join([f"{r[0]}: {r[1]}" for r in rows])
    await update.message.reply_text(text)

# /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Use /report <text> to submit a report.")
        return
    await db.execute("INSERT INTO reports(user_id, username, text, created_at) VALUES(?,?,?,?)",
                     (user.id, user.username or "", text, utils.now_iso()))
    await update.message.reply_text("Report submitted. Thank you.")

# /edquiz and /quiz and scoring
async def edquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # Bulk format: each quiz block separated by blank line:
    # Q: question
    # A) choice
    # B) choice
    # C) choice
    # D) choice
    # Answer: A
    text = update.message.text
    if text.startswith("/edquiz"):
        text = text[len("/edquiz"):].strip()
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    count = 0
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        q = ""
        a=b=c=d=ans=None
        for line in lines:
            if line.lower().startswith("q:"):
                q = line[2:].strip()
            elif line.upper().startswith("A)"):
                a = line[2:].strip()
            elif line.upper().startswith("B)"):
                b = line[2:].strip()
            elif line.upper().startswith("C)"):
                c = line[2:].strip()
            elif line.upper().startswith("D)"):
                d = line[2:].strip()
            elif line.lower().startswith("answer:"):
                ans = line.split(":",1)[1].strip().upper()
        if q and a and b and c and d and ans:
            await db.execute(
                "INSERT INTO quizzes(question, choice_a, choice_b, choice_c, choice_d, answer, created_at) VALUES(?,?,?,?,?,?,?)",
                (q, a, b, c, d, ans, utils.now_iso())
            )
            count += 1
    await update.message.reply_text(f"Added {count} quizzes.")

# /quiz: send random quiz and expect answer via message like A/B/C/D
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = await db.fetchone("SELECT id, question, choice_a, choice_b, choice_c, choice_d, answer FROM quizzes ORDER BY RANDOM() LIMIT 1")
    if not row:
        await update.message.reply_text("No quizzes available.")
        return
    qid, question, a, b, c, d, answer = row
    # store current quiz in user_data
    context.user_data["current_quiz"] = {"id": qid, "answer": answer}
    text = f"{question}\nA) {a}\nB) {b}\nC) {c}\nD) {d}\n\nReply with A/B/C/D."
    await update.message.reply_text(text)

# handle quiz answer messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip().upper() if update.message.text else ""
    # check if user has current quiz
    cq = context.user_data.get("current_quiz")
    if cq and text in ("A","B","C","D"):
        correct = (text == cq["answer"].upper())
        if correct:
            # increment score
            row = await db.fetchone("SELECT score FROM quiz_scores WHERE user_id=?", (user.id,))
            if row:
                await db.execute("UPDATE quiz_scores SET score = score + 1 WHERE user_id=?", (user.id,))
            else:
                await db.execute("INSERT INTO quiz_scores(user_id, username, score) VALUES(?,?,?)", (user.id, user.username or "", 1))
            await update.message.reply_text("Correct! ✅")
        else:
            await update.message.reply_text(f"Wrong. Correct answer: {cq['answer']}")
        context.user_data.pop("current_quiz", None)
        return
    # not a quiz answer — ignore or handle other text commands
    # fallback
    return

# /tops
async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db.fetchall("SELECT username, score FROM quiz_scores ORDER BY score DESC LIMIT 10")
    if not rows:
        await update.message.reply_text("No quiz scores yet.")
        return
    text = "\n".join([f"{i+1}. {r[0]} - {r[1]}" for i, r in enumerate(rows)])
    await update.message.reply_text(text)

# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    u = await db.fetchone("SELECT COUNT(*) FROM users")
    g = await db.fetchone("SELECT COUNT(*) FROM groups")
    v = await db.fetchone("SELECT COUNT(*) FROM verses")
    q = await db.fetchone("SELECT COUNT(*) FROM quizzes")
    text = f"Users: {u[0]}\nGroups: {g[0]}\nVerses: {v[0]}\nQuizzes: {q[0]}"
    await update.message.reply_text(text)

# /broadcast
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return ConversationHandler.END
    await update.message.reply_text("Send the broadcast message. You may attach a photo. The message will be sent to all stored groups and users.")
    return BROADCAST_WAIT

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # get message text and optional photo
    text = update.message.caption if update.message.photo else update.message.text
    photo = None
    if update.message.photo:
        # get highest resolution
        photo_file = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await photo_file.download_to_memory(out=bio)
        bio.seek(0)
        photo = bio
    # fetch groups and users
    groups = await db.fetchall("SELECT chat_id FROM groups")
    users = await db.fetchall("SELECT user_id FROM users")
    sent = 0
    for g in groups:
        try:
            if photo:
                await context.bot.send_photo(chat_id=g[0], photo=photo, caption=text)
            else:
                await context.bot.send_message(chat_id=g[0], text=text)
            sent += 1
        except Exception:
            continue
    for u in users:
        try:
            if photo:
                await context.bot.send_photo(chat_id=u[0], photo=photo, caption=text)
            else:
                await context.bot.send_message(chat_id=u[0], text=text)
            sent += 1
        except Exception:
            continue
    await update.message.reply_text(f"Broadcast sent to {sent} chats (attempted).")
    return ConversationHandler.END

# /backup and /restore
async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # send DB file
    path = db.DB_PATH
    try:
        await update.message.reply_document(open(path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"Backup failed: {e}")

async def restore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return ConversationHandler.END
    await update.message.reply_text("Please upload the backup .db file now.")
    return RESTORE_WAIT

async def restore_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect a document
    doc = update.message.document
    if not doc:
        await update.message.reply_text("Please upload a file.")
        return ConversationHandler.END
    path = db.DB_PATH
    file = await doc.get_file()
    await file.download_to_drive(path)
    await update.message.reply_text("Database restored. Restart the bot to apply changes.")
    return ConversationHandler.END

# /allclear
async def allclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not utils.is_admin(user.id):
        await update.message.reply_text("Admin only.")
        return
    # Drop all data
    await db.execute("DELETE FROM users")
    await db.execute("DELETE FROM groups")
    await db.execute("DELETE FROM about")
    await db.execute("DELETE FROM contacts")
    await db.execute("DELETE FROM verses")
    await db.execute("DELETE FROM events")
    await db.execute("DELETE FROM birthdays")
    await db.execute("DELETE FROM prayers")
    await db.execute("DELETE FROM quizzes")
    await db.execute("DELETE FROM quiz_scores")
    await db.execute("DELETE FROM reports")
    await update.message.reply_text("All data cleared.")

# track groups when bot added to group or receives message in group
async def track_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        await db.execute("INSERT OR REPLACE INTO groups(chat_id, title, added_at) VALUES(?,?,?)",
                         (chat.id, chat.title or "", utils.now_iso()))

# register handlers function
def register(dispatcher):
    from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_cmd))
    dispatcher.add_handler(CommandHandler("about", about))
    dispatcher.add_handler(CommandHandler("edabout", edabout))
    dispatcher.add_handler(CommandHandler("contact", contact))
    dispatcher.add_handler(CommandHandler("edcontact", edcontact))
    dispatcher.add_handler(CommandHandler("verse", verse))
    dispatcher.add_handler(CommandHandler("edverse", edverse))
    dispatcher.add_handler(CommandHandler("events", events_cmd))
    dispatcher.add_handler(CommandHandler("edevents", edevents))
    dispatcher.add_handler(CommandHandler("birthday", birthday))
    dispatcher.add_handler(CommandHandler("edbirthday", edbirthday))
    dispatcher.add_handler(CommandHandler("pray", pray))
    dispatcher.add_handler(CommandHandler("praylist", praylist))
    dispatcher.add_handler(CommandHandler("report", report))
    dispatcher.add_handler(CommandHandler("edquiz", edquiz))
    dispatcher.add_handler(CommandHandler("quiz", quiz))
    dispatcher.add_handler(CommandHandler("tops", tops))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("backup", backup_cmd))
    dispatcher.add_handler(CommandHandler("restore", restore_start))
    dispatcher.add_handler(CommandHandler("allclear", allclear))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast_start))

    # Conversation handlers
    bc_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={BROADCAST_WAIT: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_send)]},
        fallbacks=[]
    )
    dispatcher.add_handler(bc_conv)

    restore_conv = ConversationHandler(
        entry_points=[CommandHandler("restore", restore_start)],
        states={RESTORE_WAIT: [MessageHandler(filters.Document.ALL, restore_receive)]},
        fallbacks=[]
    )
    dispatcher.add_handler(restore_conv)

    # track groups
    dispatcher.add_handler(MessageHandler(filters.ChatType.GROUPS, track_chat))
    # generic message handler for quiz answers and admin text commands
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
