from datetime import datetime
from config import CREATOR_TAG

def now_iso():
    return datetime.utcnow().isoformat()

def format_event(row):
    return f"**{row['title']}**\n{row['datetime']}\nLocation: {row['location']}\n{row['description']}"

def footer():
    return f"\n\nCreate by : {CREATOR_TAG}"
