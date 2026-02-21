# db.py
import sqlite3
import os
from config import DB_FILE
import threading

_lock = threading.Lock()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_conn()
        cur = conn.cursor()
        with open("data_init.sql", "r", encoding="utf-8") as f:
            cur.executescript(f.read())
        conn.commit()
        conn.close()
    # ensure initial seed data
    seed_initial_data()

def seed_initial_data():
    conn = get_conn()
    cur = conn.cursor()
    # about default
    cur.execute("SELECT COUNT(*) FROM about")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO about (id, text) VALUES (1, ?)", (
            "ကျွန်ုပ်တို့၏ အသင်းတော်သည် ခရစ်ယာန် လူငယ်များအတွက် စည်းရုံးရာ၊ ဝန်ဆောင်မှုနှင့် သင်ကြားရေး အဖွဲ့ဖြစ်ပါသည်။",))
    # sample verses (5)
    cur.execute("SELECT COUNT(*) FROM verses")
    if cur.fetchone()[0] == 0:
        verses = [
            "ယေရှုခရစ်သည် ကျွန်တော်တို့၏ အလင်းဖြစ်၏။ (John 8:12)",
            "ခင်ဗျားတို့သည် အချစ်ကို ခံစားကြပါစေ။ (1 John 4:7)",
            "ယုံကြည်ခြင်းဖြင့် ကယ်တင်ခြင်းရသည်။ (Ephesians 2:8)",
            "သခင်ကို ချီးမြှင့်၍ သာယာစေပါ။ (Psalm 100:4)",
            "အားလုံးကို ချစ်ခြင်းဖြင့် ပြုမူပါ။ (Matthew 22:39)"
        ]
        for v in verses:
            cur.execute("INSERT INTO verses (text) VALUES (?)", (v,))
    # sample quizzes (5)
    cur.execute("SELECT COUNT(*) FROM quizzes")
    if cur.fetchone()[0] == 0:
        quizzes = [
            ("ဘုရားသခင်သည် ဘယ်သူလဲ။", "တစ်ဦးတည်းသော ဘုရား", "တစ်ဦးမဟုတ်ဘူး", "တစ်ဦးတည်းသော ဘုရား", "မသိ", "A"),
            ("ယေရှုခရစ်၏ သင်ကြားချက်အဓိကမှာ?", "ချစ်ခြင်း", "စွမ်းအား", "ကြောက်ရွံ့ခြင်း", "အမြတ်", "A"),
            ("ဘုရားကျမ်းစာ၏ ပထမဆုံးစာအုပ်က ဘာလဲ?", "Genesis", "Exodus", "Leviticus", "Numbers", "A"),
            ("တရားမျှတမှုကို ဘယ်သူက သင်ကြားသလဲ?", "ယေရှု", "ပေါက်တော်", "ဆာလမန်", "မသိ", "A"),
            ("ယုံကြည်ခြင်းဖြင့် ဘာရရှိသလဲ?", "ကယ်တင်ခြင်း", "အကြွေး", "အလုပ်", "အိမ်", "A")
        ]
        for q in quizzes:
            cur.execute("INSERT INTO quizzes (question, option_a, option_b, option_c, option_d, answer) VALUES (?,?,?,?,?,?)", q)
    conn.commit()
    conn.close()

# Chat registry
def add_chat(chat_id, chat_type, title=None, username=None):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO chats (chat_id, chat_type, title, username) VALUES (?,?,?,?)",
                    (chat_id, chat_type, title, username))
        conn.commit()
        conn.close()

def get_random_verse():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT text FROM verses ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row["text"] if row else None

def get_about():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT text FROM about WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row["text"] if row else ""

def set_about(text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE about SET text=? WHERE id=1", (text,))
    conn.commit()
    conn.close()

# Contacts
def list_contacts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM contacts")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_contact(name, phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts (name, phone) VALUES (?,?)", (name, phone))
    conn.commit()
    conn.close()

def clear_all_data():
    conn = get_conn()
    cur = conn.cursor()
    tables = ["chats","contacts","events","birthdays","verses","prayers","quizzes","quiz_scores","reports"]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()

# Events
def list_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, datetime, location, note FROM events ORDER BY datetime")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_event(title, datetime_str, location, note):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (title, datetime, location, note) VALUES (?,?,?,?)",
                (title, datetime_str, location, note))
    conn.commit()
    conn.close()

# Birthdays
def list_birthdays(month=None):
    conn = get_conn()
    cur = conn.cursor()
    if month:
        cur.execute("SELECT name, day, month, note FROM birthdays WHERE month=? ORDER BY day", (month,))
    else:
        cur.execute("SELECT name, day, month, note FROM birthdays ORDER BY month, day")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_birthday(name, day, month, note):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO birthdays (name, day, month, note) VALUES (?,?,?,?)", (name, day, month, note))
    conn.commit()
    conn.close()

# Prayers
def add_prayer(user_id, username, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO prayers (user_id, username, text) VALUES (?,?,?)", (user_id, username, text))
    conn.commit()
    conn.close()

def list_prayers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, text, created_at FROM prayers ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# Quizzes
def get_random_quiz():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, question, option_a, option_b, option_c, option_d FROM quizzes ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def check_quiz_answer(qid, choice):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT answer FROM quizzes WHERE id=?", (qid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return row["answer"].upper() == choice.upper()

def add_quiz_score(user_id, username, delta):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, score FROM quiz_scores WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE quiz_scores SET score = score + ? WHERE user_id=?", (delta, user_id))
    else:
        cur.execute("INSERT INTO quiz_scores (user_id, username, score) VALUES (?,?,?)", (user_id, username, max(0, delta)))
    conn.commit()
    conn.close()

def get_top_scores(limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, score FROM quiz_scores ORDER BY score DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Reports
def add_report(user_id, username, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, username, text) VALUES (?,?,?)", (user_id, username, text))
    conn.commit()
    conn.close()

# Stats
def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chats")
    chats = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prayers")
    prayers = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM quizzes")
    quizzes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM verses")
    verses = cur.fetchone()[0]
    conn.close()
    return {"chats": chats, "prayers": prayers, "quizzes": quizzes, "verses": verses}
