from typing import List
import os

ADMIN_IDS = []  # filled from env by bot.py


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def format_event(ev: dict) -> str:
    return f"{ev['title']}\nWhen: {ev['datetime']}\nWhere: {ev['location']}\n{ev['description']}"


def format_contact(c: dict) -> str:
    return f"{c['name']} — {c['phone']}"
