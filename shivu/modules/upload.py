import urllib.request
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

WRONG_FORMAT_TEXT = """Wrong ❌️ format...  eg. /upload Img_url pikachu Pokemon 3

img_url pokemon-name series rarity-number

Use rarity numbers based on Pokémon rarity:

1️⃣ ⚪ Common (Wild Pokémon, e.g., Pidgey, Rattata)  
2️⃣ 🟣 Uncommon (Stronger wild Pokémon, e.g., Arcanine)  
3️⃣ 🟡 Rare (Starter & Pseudo-Legendaries, e.g., Charizard)  
4️⃣ 🔴 Legendary (One-of-a-kind, e.g., Articuno)  
5️⃣ 💎 Mythical (Event Pokémon, e.g., Mew, Celebi)  
6️⃣ 🌟 Ultra Beast (Extra-dimensional Pokémon, e.g., Nihilego)"""

RARITY_MAP = {
    1: "⚪ Common",
    2: "🟣 Uncommon",
    3: "🟡 Rare",
    4: "🔴 Legendary",
    5: "💎 Mythical",
    6: "🌟 Ultra Beast"
}

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, {'$inc': {'sequence_value': 1}}, return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

async def upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Only authorized trainers can add Pokémon!')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT)
            return

        pokemon_name = args[1].replace('-', ' ').title()
        series = args[2].replace('-', ' ').title()

        try:
            urllib.request.urlopen(args[0])
        except:
            await update.message.reply_text('Invalid image URL.')
            return

        try:
            rarity = RARITY_MAP[int(args[3])]
        except KeyError:
            await update.message.reply_text('Invalid rarity. Please use 1-6 based on the Pokémon anime classification.')
            return

        id = str(await get_next_sequence_number('pokemon_id')).zfill(2)

        pokemon = {
            'img_url': args[0],
            'name': pokemon_name,
            'series': series,
            'rarity': rarity,
            'id': id
        }

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=args[0],
                caption=f'<b>Pokémon Name:</b> {pokemon_name}\n<b>Series:</b> {series}\n<b>Rarity:</b> {rarity}\n<b>ID:</b> {id}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            pokemon['message_id'] = message.message_id
            await collection.insert_one(pokemon)
            await update.message.reply_text('Pokémon added successfully!')
        except:
            await collection.insert_one(pokemon)
            update.effective_message.reply_text("Pokémon added, but no Database Channel Found.")

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}\nContact: {SUPPORT_CHAT}')

async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Only authorized trainers can delete Pokémon!')
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Use: /delete ID')
            return

        pokemon = await collection.find_one_and_delete({'id': args[0]})

        if pokemon:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=pokemon['message_id'])
            await update.message.reply_text('Pokémon deleted successfully!')
        else:
            await update.message.reply_text('Pokémon not found in database!')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def update(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Only authorized trainers can update Pokémon!')
        return

    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text('Incorrect format. Use: /update id field new_value')
            return

        pokemon = await collection.find_one({'id': args[0]})
        if not pokemon:
            await update.message.reply_text('Pokémon not found.')
            return

        valid_fields = ['img_url', 'name', 'series', 'rarity']
        if args[1] not in valid_fields:
            await update.message.reply_text(f'Invalid field. Use one of: {", ".join(valid_fields)}')
            return

        if args[1] in ['name', 'series']:
            new_value = args[2].replace('-', ' ').title()
        elif args[1] == 'rarity':
            try:
                new_value = RARITY_MAP[int(args[2])]
            except KeyError:
                await update.message.reply_text('Invalid rarity. Use 1-6 based on Pokémon classification.')
                return
        else:
            new_value = args[2]

        await collection.find_one_and_update({'id': args[0]}, {'$set': {args[1]: new_value}})

        if args[1] == 'img_url':
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=pokemon['message_id'])
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=new_value,
                caption=f'<b>Pokémon Name:</b> {pokemon["name"]}\n<b>Series:</b> {pokemon["series"]}\n<b>Rarity:</b> {pokemon["rarity"]}\n<b>ID:</b> {pokemon["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            await collection.find_one_and_update({'id': args[0]}, {'$set': {'message_id': message.message_id}})
        else:
            await context.bot.edit_message_caption(
                chat_id=CHARA_CHANNEL_ID,
                message_id=pokemon['message_id'],
                caption=f'<b>Pokémon Name:</b> {pokemon["name"]}\n<b>Series:</b> {pokemon["series"]}\n<b>Rarity:</b> {pokemon["rarity"]}\n<b>ID:</b> {pokemon["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )

        await update.message.reply_text('Pokémon updated successfully!')

    except Exception as e:
        await update.message.reply_text('Error updating Pokémon. Check ID or try again later.')

UPLOAD_HANDLER = CommandHandler('upload', upload, block=False)
application.add_handler(UPLOAD_HANDLER)
DELETE_HANDLER = CommandHandler('delete', delete, block=False)
application.add_handler(DELETE_HANDLER)
UPDATE_HANDLER = CommandHandler('update', update, block=False)
application.add_handler(UPDATE_HANDLER)
