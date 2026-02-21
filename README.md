# Church Community Telegram Bot

## Setup
1. Copy `.env.example` to `.env` and fill `BOT_TOKEN` and `ADMIN_IDS`.
2. Install requirements: `pip install -r requirements.txt`
3. Run: `python bot.py`

## Admin Notes
- Admin IDs must be Telegram numeric user IDs separated by commas.
- Use `/eabout`, `/econtact`, `/eevents`, `/ebirthday` to edit content.
- Use `/broadcast` to send message/photo to all users.
- Use `/backup` to download DB; `/restore` to upload DB file.
- `/allclear` will delete all data.

## DB
- SQLite file at `data/church.db`.
