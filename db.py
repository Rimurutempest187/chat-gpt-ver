# db.py
import sqlite3
from typing import List, Tuple, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "church_bot.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # chats: store users and groups that interact with bot
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        chat_type TEXT,
        username TEXT,
        title TEXT,
        first_name TEXT,
        last_name TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # about text
    cur.execute("""
    CREATE TABLE IF NOT EXISTS about (
        id INTEGER PRIMARY KEY,
        content TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # contacts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT
    )
    """)
    # verses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )
    """)
    # events
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        datetime TEXT,
        location TEXT,
        note TEXT
    )
    """)
    # birthdays
    cur.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        day INTEGER,
        month INTEGER,
        note TEXT
    )
    """)
    # prayers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # quiz
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        opt_a TEXT,
        opt_b TEXT,
        opt_c TEXT,
        opt_d TEXT,
        answer CHAR(1)
    )
    """)
    # quiz scores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        score INTEGER DEFAULT 0
    )
    """)
    # reports
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# helper functions
def save_chat(chat: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO chats (chat_id, chat_type, username, title, first_name, last_name)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (chat.get("id"), chat.get("type"), chat.get("username"), chat.get("title"),
          chat.get("first_name"), chat.get("last_name")))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as users FROM chats WHERE chat_type='private'")
    users = cur.fetchone()["users"]
    cur.execute("SELECT COUNT(*) as groups FROM chats WHERE chat_type!='private'")
    groups = cur.fetchone()["groups"]
    conn.close()
    return {"users": users, "groups": groups}

# about
def set_about(text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM about")
    cur.execute("INSERT INTO about (content) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def get_about() -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT content FROM about ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row["content"] if row else None

# contacts
def add_contact(name: str, phone: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

def list_contacts() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM contacts")
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_contacts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM contacts")
    conn.commit()
    conn.close()

# verses
def add_verses_bulk(texts: List[str]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("INSERT INTO verses (text) VALUES (?)", [(t,) for t in texts])
    conn.commit()
    conn.close()

def random_verse() -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT text FROM verses ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row["text"] if row else None

def list_verses() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM verses")
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_verses():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM verses")
    conn.commit()
    conn.close()

# events
def add_event(title, datetime_str, location, note):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (title, datetime, location, note) VALUES (?, ?, ?, ?)",
                (title, datetime_str, location, note))
    conn.commit()
    conn.close()

def list_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, datetime, location, note FROM events ORDER BY datetime")
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM events")
    conn.commit()
    conn.close()

# birthdays
def add_birthday(name, day, month, note=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO birthdays (name, day, month, note) VALUES (?, ?, ?, ?)",
                (name, day, month, note))
    conn.commit()
    conn.close()

def birthdays_in_month(month: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, day FROM birthdays WHERE month = ? ORDER BY day", (month,))
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_birthdays():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM birthdays")
    conn.commit()
    conn.close()

# prayers
def add_prayer(user_id, username, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO prayers (user_id, username, text) VALUES (?, ?, ?)",
                (user_id, username, text))
    conn.commit()
    conn.close()

def list_prayers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, text, created_at FROM prayers ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_prayers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM prayers")
    conn.commit()
    conn.close()

# quiz
def add_quiz_bulk(questions: List[Tuple[str,str,str,str,str,str]]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("INSERT INTO quiz (question, opt_a, opt_b, opt_c, opt_d, answer) VALUES (?, ?, ?, ?, ?, ?)",
                    questions)
    conn.commit()
    conn.close()

def random_quiz():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, question, opt_a, opt_b, opt_c, opt_d FROM quiz ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def get_quiz_answer(qid: int) -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT answer FROM quiz WHERE id = ?", (qid,))
    row = cur.fetchone()
    conn.close()
    return row["answer"] if row else None

def clear_quiz():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM quiz")
    conn.commit()
    conn.close()

# scores
def add_score_if_not_exists(user_id, username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM scores WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO scores (user_id, username, score) VALUES (?, ?, 0)", (user_id, username))
        conn.commit()
    conn.close()

def increment_score(user_id, username, delta=1):
    add_score_if_not_exists(user_id, username)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE scores SET score = score + ?, username = ? WHERE user_id = ?", (delta, username, user_id))
    conn.commit()
    conn.close()

def top_scores(limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, score FROM scores ORDER BY score DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def reset_scores():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM scores")
    conn.commit()
    conn.close()

# reports
def add_report(user_id, username, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, username, text) VALUES (?, ?, ?)", (user_id, username, text))
    conn.commit()
    conn.close()

def list_reports():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, text, created_at FROM reports ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# backup / restore
def backup_db(dest_path):
    import shutil
    shutil.copyfile(DB_PATH, dest_path)

def restore_db(src_path):
    import shutil
    shutil.copyfile(src_path, DB_PATH)
