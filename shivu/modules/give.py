import html
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, user_collection

async def give_pokemon(update: Update, context: CallbackContext) -> None:
    """Allows the bot owner to give any Pokémon to any user by Pokémon ID."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Usage: `/give <user_id> <pokemon_id>`", parse_mode="Markdown")
        return

    user_id = int(args[0])
    pokemon_id = args[1]

    # Fetch user data
    user_data = await user_collection.find_one({"_id": user_id})
    if not user_data:
        await update.message.reply_text("⚠️ User not found in the database.")
        return

    # Add Pokémon to user's collection
    await user_collection.update_one(
        {"_id": user_id},
        {"$push": {"pokemon": pokemon_id}}
    )

    await update.message.reply_text(f"✅ Pokémon with ID `{pokemon_id}` has been given to user `{user_id}`.", parse_mode="Markdown")

# Register the command handler
application.add_handler(CommandHandler('give', give_pokemon, block=False))
