## File: `db.py`

import sqlite3
import asyncio
from pathlib import Path
import shutil
from datetime import datetime

class Database:
    def __init__(self, path: str = "data/church.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def _connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

    async def init(self):
        await asyncio.to_thread(self._connect)
        await asyncio.to_thread(self._ensure_tables)

    def _ensure_tables(self):
        cur = self.conn.cursor()
        cur.executescript(r"""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT
        );

        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            text TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            datetime TEXT,
            location TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            day_month TEXT  -- format MM-DD
        );

        CREATE TABLE IF NOT EXISTS prayers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            a TEXT,
            b TEXT,
            c TEXT,
            d TEXT,
            answer TEXT  -- a/b/c/d
        );

        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            score INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TEXT
        );
        """)
        self.conn.commit()

    async def execute(self, sql: str, params: tuple = ()):  # write
        def _exec():
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.conn.commit()
            return cur.lastrowid
        return await asyncio.to_thread(_exec)

    async def executemany(self, sql: str, seq_of_params):
        def _em():
            cur = self.conn.cursor()
            cur.executemany(sql, seq_of_params)
            self.conn.commit()
        return await asyncio.to_thread(_em)

    async def fetchall(self, sql: str, params: tuple = ()):  # read
        def _fetch():
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_fetch)

    async def fetchone(self, sql: str, params: tuple = ()):  # read one
        def _one():
            cur = self.conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
        return await asyncio.to_thread(_one)

    async def backup(self, dest_folder: str = "data/backups"):
        dest = Path(dest_folder)
        dest.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        target = dest / f"church_backup_{stamp}.db"
        def _copy():
            self.conn.commit()
            shutil.copy2(self.path, target)
            return str(target)
        return await asyncio.to_thread(_copy)

    async def restore_from_file(self, file_path: str):
        # Replace current DB file with supplied file path (path already saved locally)
        def _restore():
            self.conn.close()
            shutil.copy2(file_path, self.path)
            # re-open
            self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return await asyncio.to_thread(_restore)

    async def clear_all(self):
        def _clear():
            cur = self.conn.cursor()
            tables = [
                'users','settings','contacts','verses','events','birthdays','prayers','quiz_questions','quiz_scores','reports'
            ]
            for t in tables:
                cur.execute(f"DELETE FROM {t}")
            self.conn.commit()
        return await asyncio.to_thread(_clear)


# create singleton instance helper
_db = None

def get_db(path: str = "data/church.db"):
    global _db
    if _db is None:
        _db = Database(path)
    return _db
