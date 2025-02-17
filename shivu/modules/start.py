import asyncio
import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import (
    application, VIDEO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID,
    pokedex as collection, banned_users_collection
)

# Replace this with a valid thunder sticker ID
THUNDER_STICKER_ID = "CAACAgEAAxkBAAENzwABZ7H96cC6jELihegWHEJZnSxWcQYAAgMJAALjeAQAAaY1zaXqGj3iNgQ"

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command with thunder effect"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            text=f"New Trainer joined: <a href='tg://user?id={user_id}'>{escape(first_name)}</a> 🎉", 
            parse_mode='HTML'
        )
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # Send Thunder Sticker
    sticker_message = await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=THUNDER_STICKER_ID)
    
    # Wait 2 seconds before deleting it
    await asyncio.sleep(2)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sticker_message.message_id)

    # Main Welcome Message
    caption = """
    ⚡ **A sudden thunder roars...** ⚡  
    **🎮 Welcome, Trainer!**  

    I am **Pokémon Catcher Bot**! Add me to your group, and I will release wild Pokémon after every 100 messages.  
    🏆 Use `/catch` to **catch Pokémon**  
    📖 Check your collection with `/pokedex`  
    ⚔ Trade Pokémon using `/trade`  

    **Are you ready to become the ultimate Pokémon Master?**  
    """
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
        [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
         InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=VIDEO_URL,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode='markdown'
    )

async def gban(update: Update, context: CallbackContext) -> None:
    """Globally bans a user from all groups where the bot is an admin."""
    if update.effective_user.id != 123456789:  # Replace with your Owner ID
        await update.message.reply_text("❌ You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /gban <user_id>")
        return

    try:
        user_id = int(context.args[0])
        await banned_users_collection.insert_one({"user_id": user_id})
        await update.message.reply_text(f"🚨 User {user_id} has been **globally banned**.")

        # Attempt to ban the user from all groups
        async for group in db.groups.find():
            try:
                await context.bot.ban_chat_member(group["_id"], user_id)
            except:
                pass
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def ungban(update: Update, context: CallbackContext) -> None:
    """Removes a user from the global ban list."""
    if update.effective_user.id != 7678359785:  # Replace with your Owner ID
        await update.message.reply_text("❌ You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ungban <user_id>")
        return

    try:
        user_id = int(context.args[0])
        await banned_users_collection.delete_one({"user_id": user_id})
        await update.message.reply_text(f"✅ User {user_id} has been **unbanned** globally.")

        # Attempt to unban the user from all groups
        async for group in db.groups.find():
            try:
                await context.bot.unban_chat_member(group["_id"], user_id)
            except:
                pass
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def button(update: Update, context: CallbackContext) -> None:
    """Handles button clicks in the bot's menu"""
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
        **📜 Trainer's Guide:**  

        🎯 `/catch` - Catch Pokémon (group only)  
        🏆 `/pokedex` - View your caught Pokémon  
        🤝 `/trade` - Trade Pokémon with others  
        🎁 `/gift` - Gift Pokémon to another trainer (group only)  
        🌍 `/top_trainers` - View top trainers in this group  
        🏅 `/gtop` - View **global** top trainers  
        ⏳ `/changetime` - Adjust Pokémon spawn time (group only)  
        🔨 `/gban` - Ban a user from all bot groups (Admin only)  
        🔓 `/ungban` - Unban a user globally  
        """
        help_keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)
        
        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode='markdown'
        )

    elif query.data == 'back':
        caption = """
        **🎮 Welcome, Trainer!**  

        I am **Pokémon Catcher Bot**! Add me to your group, and I will release wild Pokémon after every 100 messages.  
        🏆 Use `/catch` to **catch Pokémon**  
        📖 Check your collection with `/pokedex`  
        ⚔ Trade Pokémon using `/trade`  

        **Are you ready to become the ultimate Pokémon Master?**  
        """

        keyboard = [
            [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
            [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='markdown'
        )

application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
application.add_handler(CommandHandler("start", start, block=False))
application.add_handler(CommandHandler("gban", gban, block=False))
application.add_handler(CommandHandler("ungban", ungban, block=False))
