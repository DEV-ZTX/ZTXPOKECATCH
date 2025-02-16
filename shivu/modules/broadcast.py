import os
import random
import html
import re
import time
from cachetools import TTLCache
from pymongo import ASCENDING
from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, InlineQueryHandler

from shivu import (
    application, PHOTO_URL, OWNER_ID, user_collection,
    top_global_groups_collection, group_user_totals_collection, db, pm_users
)

from shivu import sudo_users as SUDO_USERS


# MongoDB Indexing for Performance
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Caching for better performance
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)


# ✨ INLINE QUERY HANDLER ✨
async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = user_collection_cache.get(user_id) or await user_collection.find_one({'id': int(user_id)})
            user_collection_cache[user_id] = user

            if user:
                all_characters = list({v['id']: v for v in user['characters']}.values())
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    all_characters = [c for c in all_characters if regex.search(c['name']) or regex.search(c['anime'])]
            else:
                all_characters = []
        else:
            all_characters = []
    else:
        regex = re.compile(query, re.IGNORECASE) if query else None
        all_characters = (all_characters_cache.get('all_characters') or
                          await collection.find({"$or": [{"name": regex}, {"anime": regex}]} if regex else {}).to_list(length=None))
        all_characters_cache['all_characters'] = all_characters

    characters = all_characters[offset:offset+50]
    next_offset = str(offset + 50) if len(characters) > 50 else str(offset + len(characters))

    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        caption = f"<b>Look At This Character !!</b>\n\n🌸: <b>{character['name']}</b>\n🏖️: <b>{character['anime']}</b>\n<b>{character['rarity']}</b>\n🆔️: <b>{character['id']}</b>\n\n<b>Globally Guessed {global_count} Times...</b>"
        results.append(InlineQueryResultPhoto(
            thumbnail_url=character['img_url'],
            id=f"{character['id']}_{time.time()}",
            photo_url=character['img_url'],
            caption=caption,
            parse_mode='HTML'
        ))

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)


# 📊 LEADERBOARD COMMANDS 📊
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)
    leaderboard_message = "<b>🌍 TOP 10 GROUPS WHO GUESSED THE MOST CHARACTERS 🌍</b>\n\n"
    
    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))[:15] + ('...' if len(group.get('group_name', '')) > 15 else '')
        leaderboard_message += f"{i}. <b>{group_name}</b> ➾ <b>{group['count']}</b>\n"

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')


async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)
    leaderboard_message = "<b>🏆 TOP 10 USERS IN THIS GROUP 🏆</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + ('...' if len(user.get('first_name', '')) > 15 else '')
        leaderboard_message += f"{i}. <b>{first_name}</b> ➾ <b>{user['character_count']}</b>\n"

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')


async def leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)
    leaderboard_message = "<b>🏅 TOP 10 USERS WITH MOST CHARACTERS 🏅</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + ('...' if len(user.get('first_name', '')) > 15 else '')
        leaderboard_message += f"{i}. <b>{first_name}</b> ➾ <b>{user['character_count']}</b>\n"

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')


# 📢 BROADCAST FUNCTION 📢
async def broadcast(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) != str(OWNER_ID):
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message
    if not message_to_broadcast:
        await update.message.reply_text("📢 Please reply to a message to broadcast.")
        return

    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await pm_users.distinct("_id")
    recipients = set(all_chats + all_users)

    failed = sum(1 for chat_id in recipients if not await context.bot.forward_message(chat_id, message_to_broadcast.chat_id, message_to_broadcast.message_id))
    await update.message.reply_text(f"✅ Broadcast complete. Failed to send to {failed} chats/users.")


# 🚀 Registering Handlers
application.add_handler(CommandHandler("ctop", ctop, block=False))
application.add_handler(CommandHandler("top", leaderboard, block=False))
application.add_handler(CommandHandler("TopGroups", global_leaderboard, block=False))
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
application.add_handler(InlineQueryHandler(inlinequery, block=False))
