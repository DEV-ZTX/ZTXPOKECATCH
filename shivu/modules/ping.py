import time
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import application, sudo_users

async def ping(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text("🚫 This command is only for sudo users!")
        return

    start_time = time.monotonic()
    message = await update.message.reply_text("🏓 Pong...")
    end_time = time.monotonic()

    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(f"🏓 Pong! `{elapsed_time}ms`", parse_mode="Markdown")

# Add the command handler
application.add_handler(CommandHandler("ping", ping))
