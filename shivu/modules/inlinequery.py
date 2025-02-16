import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler
from shivu import user_collection, collection, application, db

# Create indexes for Pokémon collection
db.pokemon.create_index([('id', ASCENDING)])
db.pokemon.create_index([('name', ASCENDING)])
db.pokemon.create_index([('type', ASCENDING)])
db.pokemon.create_index([('rarity', ASCENDING)])

# Caching system
all_pokemon_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    # User Collection Search (if query starts with 'collection.')
    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = user_collection_cache.get(user_id) or await user_collection.find_one({'id': int(user_id)})
            user_collection_cache[user_id] = user

            if user:
                all_pokemon = list({v['id']: v for v in user['pokemon']}.values())
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    all_pokemon = [pkmn for pkmn in all_pokemon if regex.search(pkmn['name']) or regex.search(pkmn['type'])]
            else:
                all_pokemon = []
        else:
            all_pokemon = []

    else:
        # General Pokémon Search
        if query:
            regex = re.compile(query, re.IGNORECASE)
            all_pokemon = list(await collection.find({"$or": [{"name": regex}, {"type": regex}, {"id": regex}]}).to_list(length=None))
        else:
            all_pokemon = all_pokemon_cache.get('all_pokemon') or list(await collection.find({}).to_list(length=None))
            all_pokemon_cache['all_pokemon'] = all_pokemon

    # Pagination (limit to 50 Pokémon per query)
    pokemon_results = all_pokemon[offset:offset+50]
    next_offset = str(offset + 50) if len(pokemon_results) > 50 else str(offset + len(pokemon_results))

    results = []
    for pkmn in pokemon_results:
        global_count = await user_collection.count_documents({'pokemon.id': pkmn['id']})
        total_pokemon = await collection.count_documents({'type': pkmn['type']})

        if query.startswith('collection.'):
            user_pokemon_count = sum(p['id'] == pkmn['id'] for p in user['pokemon'])
            user_type_count = sum(p['type'] == pkmn['type'] for p in user['pokemon'])
            caption = (
                f"<b>Trainer <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', user['id']))}</a>'s Pokémon</b>\n\n"
                f"🔹 <b>{pkmn['name']} (x{user_pokemon_count})</b>\n"
                f"🔥 Type: <b>{pkmn['type']} ({user_type_count}/{total_pokemon})</b>\n"
                f"⭐ Rarity: <b>{pkmn['rarity']}</b>\n"
                f"🔢 Pokédex: <b>{pkmn['id']}</b>"
            )
        else:
            caption = (
                f"<b>Pokémon Found!</b>\n\n"
                f"🔹 Name: <b>{pkmn['name']}</b>\n"
                f"🔥 Type: <b>{pkmn['type']}</b>\n"
                f"⭐ Rarity: <b>{pkmn['rarity']}</b>\n"
                f"🔢 Pokédex: <b>{pkmn['id']}</b>\n"
                f"🌎 Caught Globally: <b>{global_count} times</b>"
            )

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=pkmn['img_url'],
                id=f"{pkmn['id']}_{time.time()}",
                photo_url=pkmn['img_url'],
                caption=caption,
                parse_mode='HTML'
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

application.add_handler(InlineQueryHandler(inlinequery, block=False))
