# utils.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import config

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMINS

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        if not is_admin(user.id):
            await update.message.reply_text("ဤ command ကို အသုံးပြုခွင့် မရှိပါ။ (Admin only)")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
