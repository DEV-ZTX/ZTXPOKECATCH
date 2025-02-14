class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "7678359785"
    sudo_users = ""
    GROUP_ID = -1002323856532
    TOKEN = "8111204267:AAE5iq9Z0gPE3g-n9fiCxWYmUwKklE9CPRE"
    mongo_url = "mongodb+srv://vjimmy276:<GL83MueHjvCT32m3>@cluster0.pxamg.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://graph.org/file/34ce254537a31ca2a788b-f8b59bff546af8dc58.jpg", "https://graph.org/file/0cd48cfd409203a00da74-2a919fe99dd1b238ec.jpg"]
    SUPPORT_CHAT = "https://t.me/ZTX_HEADQUATERS"
    UPDATE_CHAT = "https://t.me/TEAM_ZTX"
    BOT_USERNAME = "PokemonGuessbot"
    CHARA_CHANNEL_ID = "-1002323856532"
    api_id = 28928028

    api_hash = "b097202e877124392f4851d215fa8f3a"
    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
