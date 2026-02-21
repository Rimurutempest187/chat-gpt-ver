# utils.py
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def format_contacts(rows):
    if not rows:
        return "မည်သည့် တာဝန်ခံလည်း မရှိသေးပါ။"
    lines = []
    for r in rows:
        lines.append(f"{r['name']} - {r['phone']}")
    return "\n".join(lines)

def format_events(rows):
    if not rows:
        return "လာမည့် အစီအစဉ် မရှိသေးပါ။"
    lines = []
    for r in rows:
        lines.append(f"{r['title']} | {r['datetime']} | {r['location']} | {r['note']}")
    return "\n".join(lines)

def format_birthdays(rows):
    if not rows:
        return "ယခုလအတွင်း မွေးနေ့ မရှိပါ။"
    lines = []
    for r in rows:
        lines.append(f"{r['name']} - {r['day']}/{r['month']} {r['note'] or ''}")
    return "\n".join(lines)
