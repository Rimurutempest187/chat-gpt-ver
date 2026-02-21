# utils.py
import os
from dotenv import load_dotenv
load_dotenv("config.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip()]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
