from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shivu import user_collection, shivuu

pending_trades = {}

# 🟢 Pokémon Trading System
@shivuu.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to trade a Pokémon!")
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("You can't trade Pokémon with yourself!")
        return

    if len(message.command) != 3:
        await message.reply_text("Usage: /trade [Your Pokémon ID] [Other User's Pokémon ID]")
        return

    sender_pokemon_id, receiver_pokemon_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    if not sender or 'pokemons' not in sender:
        await message.reply_text("You don't have any Pokémon to trade!")
        return

    if not receiver or 'pokemons' not in receiver:
        await message.reply_text("The other trainer doesn't have any Pokémon to trade!")
        return

    sender_pokemon = next((p for p in sender['pokemons'] if p['id'] == sender_pokemon_id), None)
    receiver_pokemon = next((p for p in receiver['pokemons'] if p['id'] == receiver_pokemon_id), None)

    if not sender_pokemon:
        await message.reply_text("You don't have the Pokémon you're trying to trade!")
        return

    if not receiver_pokemon:
        await message.reply_text("The other trainer doesn't have the Pokémon they're trying to trade!")
        return

    pending_trades[(sender_id, receiver_id)] = (sender_pokemon_id, receiver_pokemon_id)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Confirm Trade", callback_data="confirm_trade")],
            [InlineKeyboardButton("❌ Cancel Trade", callback_data="cancel_trade")]
        ]
    )

    await message.reply_text(f"{message.reply_to_message.from_user.mention}, do you accept this trade?", reply_markup=keyboard)

@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_trade", "cancel_trade"]))
async def on_trade_callback(client, callback_query):
    receiver_id = callback_query.from_user.id

    for (sender_id, _receiver_id), (sender_pokemon_id, receiver_pokemon_id) in pending_trades.items():
        if _receiver_id == receiver_id:
            break
    else:
        await callback_query.answer("This trade request is not for you!", show_alert=True)
        return

    if callback_query.data == "confirm_trade":
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        sender_pokemon = next((p for p in sender['pokemons'] if p['id'] == sender_pokemon_id), None)
        receiver_pokemon = next((p for p in receiver['pokemons'] if p['id'] == receiver_pokemon_id), None)

        if not sender_pokemon or not receiver_pokemon:
            await callback_query.message.edit_text("One of the Pokémon in this trade is no longer available!")
            del pending_trades[(sender_id, receiver_id)]
            return

        sender['pokemons'].remove(sender_pokemon)
        receiver['pokemons'].remove(receiver_pokemon)

        sender['pokemons'].append(receiver_pokemon)
        receiver['pokemons'].append(sender_pokemon)

        await user_collection.update_one({'id': sender_id}, {'$set': {'pokemons': sender['pokemons']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'pokemons': receiver['pokemons']}})

        del pending_trades[(sender_id, receiver_id)]

        await callback_query.message.edit_text(f"Trade successful! {callback_query.message.reply_to_message.from_user.mention} received **{sender_pokemon['name']}**, and you received **{receiver_pokemon['name']}**.")

    elif callback_query.data == "cancel_trade":
        del pending_trades[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌ Trade canceled!")

# 🎁 Pokémon Gifting System
pending_gifts = {}

@shivuu.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to gift a Pokémon!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("You can't gift a Pokémon to yourself!")
        return

    if len(message.command) != 2:
        await message.reply_text("Usage: /gift [Pokémon ID]")
        return

    pokemon_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    if not sender or 'pokemons' not in sender:
        await message.reply_text("You don't have any Pokémon to gift!")
        return

    pokemon = next((p for p in sender['pokemons'] if p['id'] == pokemon_id), None)

    if not pokemon:
        await message.reply_text("You don't have this Pokémon in your collection!")
        return

    pending_gifts[(sender_id, receiver_id)] = {
        'pokemon': pokemon,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Confirm Gift", callback_data="confirm_gift")],
            [InlineKeyboardButton("❌ Cancel Gift", callback_data="cancel_gift")]
        ]
    )

    await message.reply_text(f"Do you really want to gift **{pokemon['name']}** to {message.reply_to_message.from_user.mention}?", reply_markup=keyboard)

@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_gift", "cancel_gift"]))
async def on_gift_callback(client, callback_query):
    sender_id = callback_query.from_user.id

    for (_sender_id, receiver_id), gift in pending_gifts.items():
        if _sender_id == sender_id:
            break
    else:
        await callback_query.answer("This gift request is not for you!", show_alert=True)
        return

    if callback_query.data == "confirm_gift":
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        if not sender or gift['pokemon'] not in sender['pokemons']:
            await callback_query.message.edit_text("Pokémon is no longer available for gifting!")
            del pending_gifts[(sender_id, receiver_id)]
            return

        sender['pokemons'].remove(gift['pokemon'])
        await user_collection.update_one({'id': sender_id}, {'$set': {'pokemons': sender['pokemons']}})

        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'pokemons': gift['pokemon']}})
        else:
            await user_collection.insert_one({
                'id': receiver_id,
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'pokemons': [gift['pokemon']],
            })

        del pending_gifts[(sender_id, receiver_id)]
        await callback_query.message.edit_text(f"You successfully gifted **{gift['pokemon']['name']}** to {gift['receiver_first_name']}!")

    elif callback_query.data == "cancel_gift":
        del pending_gifts[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌ Gift canceled!")
