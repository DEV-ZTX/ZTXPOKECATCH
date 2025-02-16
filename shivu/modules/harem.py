from telegram import Update
from itertools import groupby
import math
from html import escape
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import collection, user_collection, application

async def pokedex(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You have not caught any Pokémon yet.')
        else:
            await update.callback_query.edit_message_text('You have not caught any Pokémon yet.')
        return

    pokemons = sorted(user['pokemons'], key=lambda x: (x['region'], x['id']))
    pokemon_counts = {k: len(list(v)) for k, v in groupby(pokemons, key=lambda x: x['id'])}
    unique_pokemons = list({pokemon['id']: pokemon for pokemon in pokemons}.values())

    total_pages = math.ceil(len(unique_pokemons) / 15)
    if page < 0 or page >= total_pages:
        page = 0  

    pokedex_message = f"<b>{escape(update.effective_user.first_name)}'s Pokédex - Page {page+1}/{total_pages}</b>\n"

    current_pokemons = unique_pokemons[page * 15:(page + 1) * 15]
    current_grouped_pokemons = {k: list(v) for k, v in groupby(current_pokemons, key=lambda x: x['region'])}

    for region, pokemons in current_grouped_pokemons.items():
        pokedex_message += f'\n<b>{region} {len(pokemons)}/{await collection.count_documents({"region": region})}</b>\n'
        for pokemon in pokemons:
            count = pokemon_counts[pokemon['id']]
            pokedex_message += f'{pokemon["id"]} {pokemon["name"]} ×{count}\n'

    total_count = len(user['pokemons'])
    keyboard = [[InlineKeyboardButton(f"See Pokédex ({total_count})", switch_inline_query_current_chat=f"pokedex.{user_id}")]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"pokedex:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"pokedex:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'favorites' in user and user['favorites']:
        fav_pokemon_id = user['favorites'][0]
        fav_pokemon = next((p for p in user['pokemons'] if p['id'] == fav_pokemon_id), None)

        if fav_pokemon and 'img_url' in fav_pokemon:
            if update.message:
                await update.message.reply_photo(photo=fav_pokemon['img_url'], parse_mode='HTML', caption=pokedex_message, reply_markup=reply_markup)
            else:
                if update.callback_query.message.caption != pokedex_message:
                    await update.callback_query.edit_message_caption(caption=pokedex_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(pokedex_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if update.callback_query.message.text != pokedex_message:
                    await update.callback_query.edit_message_text(pokedex_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['pokemons']:
            random_pokemon = random.choice(user['pokemons'])
            if 'img_url' in random_pokemon:
                if update.message:
                    await update.message.reply_photo(photo=random_pokemon['img_url'], parse_mode='HTML', caption=pokedex_message, reply_markup=reply_markup)
                else:
                    if update.callback_query.message.caption != pokedex_message:
                        await update.callback_query.edit_message_caption(caption=pokedex_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.message:
                    await update.message.reply_text(pokedex_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if update.callback_query.message.text != pokedex_message:
                        await update.callback_query.edit_message_text(pokedex_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("Your Pokédex is empty!")

async def pokedex_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("This is not your Pokédex!", show_alert=True)
        return

    await pokedex(update, context, page)

application.add_handler(CommandHandler(["pokedex", "collection"], pokedex, block=False))
pokedex_handler = CallbackQueryHandler(pokedex_callback, pattern='^pokedex', block=False)
application.add_handler(pokedex_handler)
