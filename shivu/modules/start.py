import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import application, VIDEO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pokedex as collection

async def start(update: Update, context: CallbackContext) -> None:
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

    if update.effective_chat.type == "private":
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

        await context.bot.send_video(chat_id=update.effective_chat.id, video=VIDEO_URL, caption=caption, reply_markup=reply_markup, parse_mode='markdown')

    else:
        keyboard = [
            [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
            [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_video(chat_id=update.effective_chat.id, video=VIDEO_URL, caption="🎴 I'm active! Chat with me in PM for more info.", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
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
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
