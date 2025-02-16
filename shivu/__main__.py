import time
import random
import asyncio
import re
from shivu import give
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import (
    collection, top_global_groups_collection, group_user_totals_collection, 
    user_collection, user_totals_collection, shivuu, application, LOGGER
)

locks = {}
last_pokemon = {}
caught_pokemon = {}
first_catchers = {}
warned_users = {}
message_counts = {}

RARITY_CATCH_RATE = {
    "Common": 80,
    "Rare": 60,
    "Legendary": 40,
    "Mythical": 25,
    "Ultra Beast": 10,
}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    """Monitors messages and spawns a Pokémon after a set frequency."""
    chat_id = str(update.effective_chat.id)

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_data = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_data.get('message_frequency', 100) if chat_data else 100

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        if message_counts[chat_id] % message_frequency == 0:
            await spawn_pokemon(update, context)
            message_counts[chat_id] = 0

async def spawn_pokemon(update: Update, context: CallbackContext) -> None:
    """Spawns a Pokémon with an image but without revealing its name."""
    chat_id = update.effective_chat.id
    all_pokemon = list(await collection.find({}).to_list(length=None))
    
    if chat_id not in caught_pokemon:
        caught_pokemon[chat_id] = []

    if len(caught_pokemon[chat_id]) == len(all_pokemon):
        caught_pokemon[chat_id] = []

    pokemon = random.choice([p for p in all_pokemon if p['id'] not in caught_pokemon[chat_id]])

    caught_pokemon[chat_id].append(pokemon['id'])
    last_pokemon[chat_id] = pokemon

    if chat_id in first_catchers:
        del first_catchers[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=pokemon['img_url'],
        caption="📢 A wild Pokémon has appeared!\n❓ Try to catch it using `/catch <Pokémon Name>`",
        parse_mode='Markdown'
    )

async def catch_pokemon(update: Update, context: CallbackContext) -> None:
    """Handles Pokémon catching based on user input."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_pokemon:
        return

    if chat_id in first_catchers:
        await update.message.reply_text("❌ Someone already caught this Pokémon! Try again next time.")
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    pokemon_name = last_pokemon[chat_id]['name'].lower()

    if sorted(pokemon_name.split()) == sorted(guess.split()) or pokemon_name == guess:
        rarity = last_pokemon[chat_id]["rarity"]
        catch_rate = RARITY_CATCH_RATE.get(rarity, 50)
        if random.randint(1, 100) > catch_rate:
            await update.message.reply_text("⚠️ The Pokémon escaped! Try again next time.")
            return
        
        first_catchers[chat_id] = user_id
        user = await user_collection.find_one({'id': user_id})
        
        if user:
            await user_collection.update_one({'id': user_id}, {'$push': {'pokemon': last_pokemon[chat_id]}})
        else:
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'pokemon': [last_pokemon[chat_id]],
            })

        await group_user_totals_collection.update_one(
            {'user_id': user_id, 'group_id': chat_id}, 
            {'$inc': {'catch_count': 1}}, 
            upsert=True
        )
        
        await top_global_groups_collection.update_one(
            {'group_id': chat_id}, 
            {'$inc': {'catch_count': 1}}, 
            upsert=True
        )

        keyboard = [[InlineKeyboardButton(f"View Collection", switch_inline_query_current_chat=f"collection.{user_id}")]]
        
        await update.message.reply_text(
            f"<b>{escape(update.effective_user.first_name)}</b> caught a Pokémon! ✅ 🎉\n"
            f"🔹 **Name:** <b>{last_pokemon[chat_id]['name']}</b>\n"
            f"🌟 **Rarity:** <b>{last_pokemon[chat_id]['rarity']}</b>\n\n"
            f"Use /collection to view your Pokémon.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("❌ Incorrect Pokémon name! Try again.")

async def collection(update: Update, context: CallbackContext) -> None:
    """Displays a user's Pokémon collection."""
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or "pokemon" not in user:
        await update.message.reply_text("You haven't caught any Pokémon yet. Use /catch to start!")
        return

    pokemon_list = "\n".join([f"{p['name']} ({p['rarity']})" for p in user['pokemon']])
    await update.message.reply_text(f"📜 <b>{escape(update.effective_user.first_name)}'s Pokémon Collection:</b>\n{pokemon_list}", parse_mode='HTML')

async def stats(update: Update, context: CallbackContext) -> None:
    """Displays bot stats."""
    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')

    await update.message.reply_text(f'Total Trainers: {user_count}\nTotal Active Groups: {len(group_count)}')

def main() -> None:
    """Runs the bot."""
    application.add_handler(CommandHandler("catch", catch_pokemon, block=False))
    application.add_handler(CommandHandler("collection", collection, block=False))
    application.add_handler(CommandHandler("stats", stats, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Pokémon Bot Started")
    main()
