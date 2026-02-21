# utils.py
import os
from datetime import datetime
from typing import List

def get_admin_ids():
    raw = os.getenv("ADMIN_IDS", "")
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]

def is_admin(user_id: int):
    return user_id in get_admin_ids()

def now_iso():
    return datetime.utcnow().isoformat()

def parse_bulk_lines(text: str) -> List[str]:
    # Accepts many lines; ignore empty lines; strip each
    return [line.strip() for line in text.splitlines() if line.strip()]
