import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    LOGGER = True

    OWNER_ID = os.getenv("OWNER_ID")
    SUDO_USERS = os.getenv("SUDO_USERS", "").split()
    GROUP_ID = int(os.getenv("GROUP_ID", "-1002323856532"))
    TOKEN = os.getenv("TOKEN")
    MONGO_URL = os.getenv("MONGO_URL")
    PHOTO_URL = os.getenv("PHOTO_URL", "").split(",")
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT")
    UPDATE_CHAT = os.getenv("UPDATE_CHAT")
    BOT_USERNAME = os.getenv("BOT_USERNAME")
    CHARA_CHANNEL_ID = os.getenv("CHARA_CHANNEL_ID")

    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")

class Production(Config):
    LOGGER = True

class Development(Config):
    LOGGER = True
