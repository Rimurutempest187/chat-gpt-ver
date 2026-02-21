# db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/church.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # settings: about, contact, events_text
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    # verses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL
    )""")
    # events
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        datetime TEXT,
        location TEXT,
        note TEXT
    )""")
    # birthdays
    cur.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        day INTEGER,
        month INTEGER,
        note TEXT
    )""")
    # prayers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    # quizzes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        choice_a TEXT,
        choice_b TEXT,
        choice_c TEXT,
        choice_d TEXT,
        answer CHAR(1)
    )""")
    # quiz scores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        score INTEGER DEFAULT 0
    )""")
    # reports
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    # groups (for broadcast)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        title TEXT
    )""")
    # users (for stats)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def backup_db(backup_path: str):
    conn = get_conn()
    with open(backup_path, "wb") as f:
        for chunk in conn.iterdump():
            f.write((chunk + "\n").encode("utf-8"))
    conn.close()

def restore_db_from_dump(dump_path: str):
    conn = get_conn()
    cur = conn.cursor()
    with open(dump_path, "r", encoding="utf-8") as f:
        sql = f.read()
    cur.executescript(sql)
    conn.commit()
    conn.close()
