# db.py
import sqlite3
import shutil
import os

DB_NAME = "church.db"
BACKUP_NAME = "church_backup.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users Table (For Broadcast and Stats)
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER DEFAULT 0)''')
    # Settings Table (For About, Contact, Events, etc.)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    # Prayer List
    c.execute('''CREATE TABLE IF NOT EXISTS prayers (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, request TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_setting(key, default_msg="အချက်အလက် မရှိသေးပါ။"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default_msg

def update_setting(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_prayer(username, request):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO prayers (username, request) VALUES (?, ?)", (username, request))
    conn.commit()
    conn.close()

def get_prayers():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, request FROM prayers")
    results = c.fetchall()
    conn.close()
    return results

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    results = [row[0] for row in c.fetchall()]
    conn.close()
    return results

def add_score(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET score = score + 10 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_top_scores():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT 10")
    results = c.fetchall()
    conn.close()
    return results

def backup_db():
    shutil.copyfile(DB_NAME, BACKUP_NAME)

def restore_db():
    if os.path.exists(BACKUP_NAME):
        shutil.copyfile(BACKUP_NAME, DB_NAME)
        return True
    return False

def clear_all():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
