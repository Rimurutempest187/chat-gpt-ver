# Church Community Telegram Bot

## Setup
1. Create bot token via @BotFather.
2. Create `.env` file with:
3. Install:
4. Run:

## Admin usage
- Use admin commands from the admin Telegram account(s) listed in `ADMIN_IDS`.
- Bulk add verses: send `/edverse` followed by verses each on a new line (or send a message where each line is a verse).
- Bulk add quizzes: send `/edquiz` then blocks separated by blank lines. Each block:
- Broadcast: `/broadcast` then send the message (optionally attach a photo). The bot will attempt to send to stored groups and users.

## Data
- Database file: `data/church.db`
- Backup: `/backup` (admin) sends the DB file.
- Restore: `/restore` (admin) then upload DB file.

