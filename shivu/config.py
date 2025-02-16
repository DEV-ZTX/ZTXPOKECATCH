import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    LOGGER = True

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Default to 0 if missing
    SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split())) if os.getenv("SUDO_USERS") else []
    GROUP_ID = int(os.getenv("GROUP_ID", "-1002323856532"))
    TOKEN = os.getenv("TOKEN") or "YOUR_DEFAULT_TOKEN"
    MONGO_URL = os.getenv("MONGO_URL") or "YOUR_DEFAULT_MONGO_URL"
    PHOTO_URL = os.getenv("PHOTO_URL", "").split(",") if os.getenv("PHOTO_URL") else []
    VIDEO_URL = os.getenv("VIDEO_URL", "https://example.com/specific_video.mp4")  # Add Video URL here
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/default_support")
    UPDATE_CHAT = os.getenv("UPDATE_CHAT", "https://t.me/default_updates")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "DefaultBot")
    CHARA_CHANNEL_ID = int(os.getenv("CHARA_CHANNEL_ID", "-1002323856532"))
    
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "default_hash")

class Production(Config):
    LOGGER = True

class Development(Config):
    LOGGER = True
