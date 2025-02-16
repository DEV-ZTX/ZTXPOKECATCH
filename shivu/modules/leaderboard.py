import os
import random
import html
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import (application, PHOTO_URL, OWNER_ID, 
                    user_collection, top_global_groups_collection, 
                    group_user_totals_collection, sudo_users as SUDO_USERS)  

async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    """Shows the top 10 groups with the most Pokémon caught globally."""
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>🏆 TOP 10 GROUPS - Pokémon Caught</b>\n\n"
    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count} Pokémon</b>\n'

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')

async def ctop(update: Update, context: CallbackContext) -> None:
    """Shows top 10 trainers who caught the most Pokémon in a group."""
    chat_id = update.effective_chat.id
    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "pokemon_count": "$count"}},
        {"$sort": {"pokemon_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>🏅 TOP 10 TRAINERS in this Group</b>\n\n"
    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
        pokemon_count = user['pokemon_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{pokemon_count} Pokémon</b>\n'

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')

async def leaderboard(update: Update, context: CallbackContext) -> None:
    """Shows the top 10 trainers with the most Pokémon collected globally."""
    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "pokemon_count": {"$size": "$pokemon"}}},
        {"$sort": {"pokemon_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>🌍 GLOBAL TOP 10 TRAINERS</b>\n\n"
    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
        pokemon_count = user['pokemon_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{pokemon_count} Pokémon</b>\n'

    await update.message.reply_photo(photo=random.choice(PHOTO_URL), caption=leaderboard_message, parse_mode='HTML')

async def stats(update: Update, context: CallbackContext) -> None:
    """Shows total number of trainers and groups using the bot (Only for Owner)."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')

    await update.message.reply_text(f'👥 Total Trainers: {user_count}\n🏘️ Total Groups: {len(group_count)}')

async def send_users_document(update: Update, context: CallbackContext) -> None:
    """Allows sudo users to download a list of all trainers."""
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('🔒 Only for Sudo users...')
        return

    cursor = user_collection.find({})
    users = [doc async for doc in cursor]
    with open('users.txt', 'w') as f:
        f.write("\n".join([user['first_name'] for user in users]))
    
    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('users.txt')

async def send_groups_document(update: Update, context: CallbackContext) -> None:
    """Allows sudo users to download a list of all groups using the bot."""
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('🔒 Only for Sudo users...')
        return

    cursor = top_global_groups_collection.find({})
    groups = [doc async for doc in cursor]
    with open('groups.txt', 'w') as f:
        f.write("\n".join([group['group_name'] for group in groups]))
    
    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('groups.txt')

# Register Commands
application.add_handler(CommandHandler('ctop', ctop, block=False))  # Top 10 trainers in a group
application.add_handler(CommandHandler('stats', stats, block=False))  # Bot stats (owner only)
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))  # Top 10 groups globally
application.add_handler(CommandHandler('list', send_users_document, block=False))  # Export users (sudo only)
application.add_handler(CommandHandler('groups', send_groups_document, block=False))  # Export groups (sudo only)
application.add_handler(CommandHandler('top', leaderboard, block=False))  # Global top 10 trainers
