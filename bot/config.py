# bot/config.py
#Handles configuration management, loading environment variables, and managing persistent configurations through config.json.
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

from .logger import logger

# Load environment variables from .env file
load_dotenv()

# Path to the config.json file
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / 'config.json'

# Load environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"https://yourdomain.com/{BOT_TOKEN}")

USE_WEBHOOK = os.getenv("USE_WEBHOOK", "False").lower() == "true"

# Parse ADMINS
admins_env = os.getenv("ADMINS", "")
ADMINS: List[int] = []
if admins_env:
    try:
        ADMINS = [int(uid.strip()) for uid in admins_env.split(",") if uid.strip().isdigit()]
    except ValueError:
        logger.error("ADMINS environment variable contains non-integer values. Using an empty admin list.")
else:
    logger.warning("ADMINS environment variable is not set. Using an empty admin list.")

# Initialize or load configurations
default_config = {
    "blocked_users": [],
    "user_sessions": {},
    "telegram_api_id": None,
    "telegram_api_hash": None,
    "telegram_string_session": None,
    "target_channel_username": None,
    "apify_api_token": None
}

if CONFIG_FILE.exists():
    with CONFIG_FILE.open('r', encoding='utf-8') as f:
        try:
            config = json.load(f)
            # Ensure all keys are present
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
        except json.JSONDecodeError:
            logger.error("config.json is corrupted. Resetting configurations.")
            config = default_config.copy()
            with CONFIG_FILE.open('w', encoding='utf-8') as fw:
                json.dump(config, fw, indent=4, ensure_ascii=False)
else:
    config = default_config.copy()
    with CONFIG_FILE.open('w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def save_config():
    """
    Save the current configuration to config.json.
    """
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Configuration saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")

def is_admin(user_id: int) -> bool:
    """
    Check if a user is an admin.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        bool: True if the user is an admin, False otherwise.
    """
    return user_id in ADMINS

def get_session(user_id: int) -> Dict[str, Any]:
    """
    Retrieve session data for a user.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        dict: Session data.
    """
    return config.get("user_sessions", {}).get(str(user_id), {})

def set_session(user_id: int, session_data: Dict[str, Any]):
    """
    Set session data for a user.

    Args:
        user_id (int): Telegram user ID.
        session_data (dict): Session data to set.
    """
    if "user_sessions" not in config:
        config["user_sessions"] = {}
    config["user_sessions"][str(user_id)] = session_data
    save_config()

__all__ = ['BOT_TOKEN', 'WEBHOOK_URL', 'USE_WEBHOOK', 'ADMINS', 'config', 'save_config',
           'is_admin', 'get_session', 'set_session']
#Key Features:
#
#Environment Variables: Loaded using python-dotenv.
#Persistent Configuration: Managed through config.json.
#Admin Management: Parses and validates admin user IDs.
#Session Management: Handles user-specific sessions for conversational states.
#Important: Sensitive information such as APIFY_API_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_STRING_SESSION, and TARGET_CHANNEL_USERNAME are managed via the bot's interface and stored securely in config.json.
