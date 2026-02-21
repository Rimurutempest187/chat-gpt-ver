import sqlite3
from typing import List, Tuple, Optional
import os
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_at TEXT
    )
    """)
    # about (single row)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS about (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        content TEXT
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
    # daily verses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        verse TEXT,
        date TEXT
    )
    """)
    # events
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        datetime TEXT,
        location TEXT,
        description TEXT
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
        created_at TEXT
    )
    """)
    # prayer list (same as prayers)
    # quiz questions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        choice_a TEXT,
        choice_b TEXT,
        choice_c TEXT,
        choice_d TEXT,
        answer CHAR(1)
    )
    """)
    # quiz scores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        user_id INTEGER,
        username TEXT,
        score INTEGER,
        PRIMARY KEY (user_id)
    )
    """)
    # reports
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_user(user_id:int, username:str, first_name:str, last_name:str, joined_at:str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (id, username, first_name, last_name, joined_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, first_name, last_name, joined_at))
    conn.commit()
    conn.close()

# Simple wrappers for CRUD used by handlers
def get_about() -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT content FROM about WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row["content"] if row else None

def set_about(content:str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO about (id, content) VALUES (1, ?)", (content,))
    conn.commit()
    conn.close()

def list_contacts() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contacts ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_contact(name, phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

def clear_all_data():
    conn = get_conn()
    cur = conn.cursor()
    tables = ["users","about","contacts","verses","events","birthdays","prayers","quiz","scores","reports"]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()

def export_db_bytes() -> bytes:
    with open(DB_PATH, "rb") as f:
        return f.read()

def import_db_bytes(data: bytes):
    with open(DB_PATH, "wb") as f:
        f.write(data)

# Additional DB helpers for verses, events, birthdays, prayers, quiz, scores, reports
def add_verse(verse, date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO verses (verse, date) VALUES (?, ?)", (verse, date))
    conn.commit()
    conn.close()

def get_today_verses(date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM verses WHERE date = ?", (date,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_event(title, datetime_str, location, description):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (title, datetime, location, description) VALUES (?, ?, ?, ?)",
                (title, datetime_str, location, description))
    conn.commit()
    conn.close()

def list_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY datetime")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_birthday(name, day, month, note):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO birthdays (name, day, month, note) VALUES (?, ?, ?, ?)", (name, day, month, note))
    conn.commit()
    conn.close()

def birthdays_this_month(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM birthdays WHERE month = ?", (month,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_prayer(user_id, username, text, created_at):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO prayers (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, text, created_at))
    conn.commit()
    conn.close()

def list_prayers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prayers ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_quiz_question(q, a, b, c, d, ans):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO quiz (question, choice_a, choice_b, choice_c, choice_d, answer) VALUES (?, ?, ?, ?, ?, ?)",
                (q, a, b, c, d, ans))
    conn.commit()
    conn.close()

def get_random_quiz():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quiz ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def update_score(user_id, username, delta):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT score FROM scores WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        new = row["score"] + delta
        cur.execute("UPDATE scores SET score = ?, username = ? WHERE user_id = ?", (new, username, user_id))
    else:
        cur.execute("INSERT INTO scores (user_id, username, score) VALUES (?, ?, ?)", (user_id, username, delta))
    conn.commit()
    conn.close()

def top_scores(limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scores ORDER BY score DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_report(user_id, username, text, created_at):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, text, created_at))
    conn.commit()
    conn.close()
