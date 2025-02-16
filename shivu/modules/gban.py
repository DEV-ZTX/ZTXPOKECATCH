from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, banned_users_collection
from shivu.utils import is_owner, get_bot_admin_groups

async def gban(update: Update, context: CallbackContext) -> None:
    """Globally bans a user from all groups where the bot is an admin."""
    if not await is_owner(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please specify a user ID or reply to a user.")
        return

    try:
        user_id = int(context.args[0]) if context.args else update.message.reply_to_message.from_user.id
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    if await banned_users_collection.find_one({"user_id": user_id}):
        await update.message.reply_text("🚫 This user is already globally banned.")
        return

    await banned_users_collection.insert_one({"user_id": user_id})

    groups = await get_bot_admin_groups(context)
    for group_id in groups:
        try:
            await context.bot.ban_chat_member(group_id, user_id)
        except Exception as e:
            print(f"Failed to ban user {user_id} in group {group_id}: {e}")

    await update.message.reply_text(f"✅ User {user_id} has been globally banned.")

async def ungban(update: Update, context: CallbackContext) -> None:
    """Removes a user from the global ban list."""
    if not await is_owner(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please specify a user ID.")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    if not await banned_users_collection.find_one({"user_id": user_id}):
        await update.message.reply_text("⚠️ This user is not globally banned.")
        return

    await banned_users_collection.delete_one({"user_id": user_id})

    groups = await get_bot_admin_groups(context)
    for group_id in groups:
        try:
            await context.bot.unban_chat_member(group_id, user_id)
        except Exception as e:
            print(f"Failed to unban user {user_id} in group {group_id}: {e}")

    await update.message.reply_text(f"✅ User {user_id} has been globally unbanned.")

# Add handlers
application.add_handler(CommandHandler("gban", gban, block=False))
application.add_handler(CommandHandler("ungban", ungban, block=False))
