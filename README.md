

## **Project Structure**

Organizing your project effectively is crucial for maintainability and scalability. Here's the recommended directory structure:

```
telegram_bot/
├── bot/
│   ├── __init__.py
│   ├── adder.py
│   ├── checker.py
│   ├── config.py
│   ├── file_handler.py
│   ├── handlers.py
│   ├── logger.py
│   └── main.py
├── logs/
│   └── bot.log
├── tests/
│   ├── __init__.py
│   ├── test_adder.py
│   └── test_checker.py
├── .env
├── config.json
├── requirements.txt
└── README.md
```

- **`bot/`**: Contains all bot-related modules.
- **`logs/`**: Stores log files for debugging and monitoring.
- **`tests/`**: Contains unit tests for critical components.
- **`.env`**: Stores environment variables (should be kept secure and not version-controlled).
- **`config.json`**: Holds persistent configurations.
- **`requirements.txt`**: Lists all Python dependencies.
- **`README.md`**: Provides an overview and setup instructions.

---

## **1. Dependencies**

Ensure all necessary dependencies are listed in `requirements.txt`:

```txt
# requirements.txt

python-telegram-bot==20.3
telethon==1.31.0
apify-client==0.0.10
python-dotenv==1.0.0
```

**Installation:**

```bash
pip install -r requirements.txt
```

---

## **2. Environment Configuration**

Create a `.env` file at the root of your project to store non-sensitive environment variables. **Ensure this file is added to `.gitignore` to prevent it from being version-controlled.**

```env
# .env

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
WEBHOOK_URL=https://yourdomain.com/your_bot_token_here
ADMINS=123456789,987654321  # Comma-separated Telegram User IDs
USE_WEBHOOK=False
```

**Notes:**

- **`TELEGRAM_BOT_TOKEN`**: Obtain this from [BotFather](https://t.me/BotFather) on Telegram.
- **`WEBHOOK_URL`**: Required if using webhooks. Ensure your server has a valid SSL certificate.
- **`ADMINS`**: List of Telegram user IDs authorized to interact with the bot.
- **`USE_WEBHOOK`**: Set to `True` to use webhooks; otherwise, the bot will use polling.

**Important:** Sensitive information such as `APIFY_API_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_STRING_SESSION`, and `TARGET_CHANNEL_USERNAME` will be managed via the bot's interface and stored securely in `config.json`.

---

## **3. Codebase**

Let's delve into each component of the bot.

### **3.1 `bot/__init__.py`**

This file designates the `bot` directory as a Python package. It can be left empty or used for package-level initializations if necessary.

```python
# bot/__init__.py

# This file makes the 'bot' directory a Python package.
# You can include package-level initializations here if necessary.
```

---

### **3.2 `bot/logger.py`**

Configures the logging mechanism, ensuring that logs are written to a file with rotation to prevent uncontrolled growth.

```python
# bot/logger.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Determine the directory where the script is located
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure the logs directory exists
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Define the log file path
LOG_FILE = LOG_DIR / "bot.log"

# Configure logging with rotation to prevent log file from growing indefinitely
logger = logging.getLogger("TelegramBot")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

**Key Features:**

- **Rotating File Handler**: Limits log file size to 5MB with up to 5 backups.
- **Structured Logging**: Includes timestamps, log levels, and messages for clarity.

---

### **3.3 `bot/config.py`**

Handles configuration management, loading environment variables, and managing persistent configurations through `config.json`.

```python
# bot/config.py

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
```

**Key Features:**

- **Environment Variables**: Loaded using `python-dotenv`.
- **Persistent Configuration**: Managed through `config.json`.
- **Admin Management**: Parses and validates admin user IDs.
- **Session Management**: Handles user-specific sessions for conversational states.

**Important:** Sensitive information such as `APIFY_API_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_STRING_SESSION`, and `TARGET_CHANNEL_USERNAME` are managed via the bot's interface and stored securely in `config.json`.

---

### **3.4 `bot/checker.py`**

Uses the Apify service to verify if phone numbers are registered on Telegram.

```python
# bot/checker.py

import csv
from typing import List, Dict, Any
import time

from apify_client import ApifyClient
from .logger import logger

class TelegramChecker:
    """
    A class to check if phone numbers are registered on Telegram using Apify.
    """

    def __init__(self, api_token: str, proxy_config: Dict[str, Any] = None):
        """
        Initialize the TelegramChecker with API token and optional proxy configuration.

        Args:
            api_token (str): Your Apify API token.
            proxy_config (dict, optional): Proxy configuration for Apify. Defaults to None.
        """
        self.client = ApifyClient(api_token)
        self.proxy_config = proxy_config or {"useApifyProxy": True, "apifyProxyGroups": ["SHADER"]}
        logger.info("TelegramChecker initialized.")

    def read_csv(self, file_path: str) -> List[str]:
        """
        Read phone numbers from a CSV file.

        Args:
            file_path (str): Path to the CSV file.

        Returns:
            list: List of phone numbers.
        """
        phone_numbers = []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row:
                        phone = row[0].strip()
                        if phone:
                            phone_numbers.append(phone)
            logger.info(f"Read {len(phone_numbers)} phone numbers from CSV.")
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
        return phone_numbers

    def check_telegram_status(self, phone_numbers: List[str]) -> List[Dict[str, Any]]:
        """
        Check if phone numbers are registered on Telegram.

        Args:
            phone_numbers (list): List of phone numbers to check.

        Returns:
            list: Results from the Telegram checker.
        """
        results = []
        for i in range(0, len(phone_numbers), 10):  # Process in batches of 10
            batch = phone_numbers[i:i+10]
            logger.info(f"Checking batch: {batch}")
            run_input = {
                "phoneNumbers": batch,
                "proxyConfiguration": self.proxy_config
            }
            try:
                run = self.client.actor("wilcode/telegram-phone-number-checker").call(run_input=run_input)
                run_id = run["id"]
                logger.info(f"Actor run started with run_id: {run_id}")

                # Wait for the actor run to finish
                run_finished = False
                while not run_finished:
                    run_info = self.client.run(run_id).get()
                    status = run_info.get('status')
                    logger.info(f"Actor run status: {status}")
                    if status == 'SUCCEEDED':
                        run_finished = True
                    elif status in ['FAILED', 'TIMED_OUT', 'CANCELED']:
                        logger.error(f"Actor run failed with status: {status}")
                        break
                    else:
                        logger.info("Waiting for 10 seconds before checking run status again.")
                        time.sleep(10)  # Sleep for 10 seconds before checking again

                if run_finished:
                    dataset_id = run_info["defaultDatasetId"]
                    dataset = self.client.dataset(dataset_id)
                    dataset_items = dataset.iterate_items()
                    for item in dataset_items:
                        results.append(item)
                    logger.info(f"Batch {i//10 + 1} processed successfully.")
                else:
                    logger.error(f"Actor run for batch {batch} did not complete successfully.")
            except Exception as e:
                logger.error(f"Error processing batch {batch}: {e}")
        logger.info(f"Total results obtained: {len(results)}")
        return results

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save the results to a CSV file.

        Args:
            results (list): Results from the Telegram checker.
            output_file (str): Path to the output CSV file.
        """
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(["Phone Number", "Registered on Telegram", "Telegram User ID"])
                for result in results:
                    phone = result.get("phoneNumber")
                    is_registered = result.get("isRegistered")
                    user_id = result.get("userId") if is_registered else ""
                    csv_writer.writerow([phone, is_registered, user_id])
            logger.info(f"Results saved to {output_file}.")
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {e}")

    def display_results(self, results: List[Dict[str, Any]]):
        """
        Display the results in the console.

        Args:
            results (list): Results from the Telegram checker.
        """
        logger.info("Telegram Checker Results:")
        for result in results:
            logger.info(f"Phone Number: {result.get('phoneNumber')} - Registered: {result.get('isRegistered')} - User ID: {result.get('userId', 'N/A')}")
```

**Key Features:**

- **Batch Processing**: Processes phone numbers in batches of 10 to optimize API usage.
- **Apify Integration**: Utilizes Apify actors to check Telegram registration status.
- **Error Handling**: Robustly handles potential errors during API calls.
- **Result Management**: Saves and displays results in CSV format.

---

### **3.5 `bot/adder.py`**

Uses Telethon to add users to a specified Telegram channel, handling various exceptions and rate limits.

```python
# bot/adder.py

import asyncio
from typing import List, Dict
import logging

from telethon import TelegramClient, errors, functions
from telethon.sessions import StringSession
from .logger import logger

class TelegramAdder:
    """
    A class to add users to a Telegram channel using Telethon.
    """

    def __init__(self, api_id: int, api_hash: str, string_session: str, target_channel_username: str):
        """
        Initialize the TelegramAdder with API credentials and target channel.

        Args:
            api_id (int): Telegram API ID.
            api_hash (str): Telegram API Hash.
            string_session (str): StringSession for Telethon.
            target_channel_username (str): Username of the target channel (e.g., @yourchannel).
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.string_session = string_session
        self.target_channel_username = target_channel_username
        self.client = TelegramClient(StringSession(self.string_session), self.api_id, self.api_hash)
        logger.info("TelegramAdder initialized.")

    async def connect(self):
        """
        Connect to Telegram.
        """
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.error("Telethon client is not authorized. Please ensure the bot is authorized.")
            raise ValueError("Telethon client is not authorized.")

    async def disconnect(self):
        """
        Disconnect from Telegram.
        """
        await self.client.disconnect()
        logger.info("Telethon client disconnected.")

    async def add_users_to_channel(self, user_ids: List[int], blocked_users: List[int]) -> Dict[str, List[int]]:
        """
        Add users to the target channel.

        Args:
            user_ids (list): List of Telegram user IDs to add.
            blocked_users (list): List of Telegram user IDs to block.

        Returns:
            dict: Summary of added and failed users.
        """
        summary = {
            "added": [],
            "failed": []
        }
        try:
            target_channel = await self.client.get_entity(self.target_channel_username)
            logger.info(f"Target channel {self.target_channel_username} retrieved.")
        except ValueError:
            logger.error(f"Target channel {self.target_channel_username} not found. Please verify the username.")
            raise ValueError(f"Target channel {self.target_channel_username} not found. Please verify the username.")
        except errors.ChatAdminRequiredError:
            logger.error(f"Bot lacks admin permissions in the target channel {self.target_channel_username}.")
            raise PermissionError(f"Bot lacks admin permissions in the target channel {self.target_channel_username}.")
        except Exception as e:
            logger.error(f"Failed to get target channel {self.target_channel_username}: {e}")
            raise ValueError(f"Failed to get target channel {self.target_channel_username}: {e}")

        for user_id in user_ids:
            if user_id in blocked_users:
                logger.info(f"User {user_id} is blocked. Skipping.")
                continue
            try:
                user = await self.client.get_entity(user_id)
                await self.client(functions.channels.InviteToChannelRequest(
                    channel=target_channel,
                    users=[user]
                ))
                summary["added"].append(user_id)
                logger.info(f"Added user {user_id} to channel.")
                await asyncio.sleep(1)  # To respect rate limits
            except errors.FloodWaitError as e:
                logger.warning(f"Flood wait error: {e}. Sleeping for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
                summary["failed"].append(user_id)
                continue
            except errors.UserPrivacyRestrictedError:
                logger.warning(f"User {user_id} has privacy settings that prevent adding to channels.")
                summary["failed"].append(user_id)
                continue
            except errors.UserAlreadyParticipantError:
                logger.info(f"User {user_id} is already a participant of the channel.")
                summary["failed"].append(user_id)
                continue
            except errors.ChatWriteForbiddenError:
                logger.error(f"Bot does not have permission to write in the target channel {self.target_channel_username}.")
                summary["failed"].append(user_id)
                continue
            except Exception as e:
                logger.error(f"Failed to add user {user_id} to channel: {e}")
                summary["failed"].append(user_id)
                continue

        logger.info(f"Users added: {summary['added']}, Users failed: {summary['failed']}")
        return summary
```

**Key Features:**

- **Telethon Integration**: Manages connections and interactions with the Telegram API.
- **Error Handling**: Gracefully handles various Telethon exceptions, including rate limits.
- **Rate Limiting**: Implements delays to respect Telegram's rate limits.

---

### **3.6 `bot/file_handler.py`**

Manages file operations such as saving, deleting files, and handling directories asynchronously.

```python
# bot/file_handler.py

import asyncio
from pathlib import Path
from typing import Any
import shutil

from .logger import logger

class FileHandler:
    """
    A class to handle file operations like saving, deleting, and processing files.
    """

    def __init__(self):
        """
        Initialize the FileHandler.
        """
        logger.info("FileHandler initialized.")

    async def save_file(self, source: Path, destination: Path) -> bool:
        """
        Save a file from source to destination asynchronously.

        Args:
            source (Path): Source file path.
            destination (Path): Destination file path.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, source.rename, destination)
            logger.info(f"File saved from {source} to {destination}.")
            return True
        except Exception as e:
            logger.error(f"Failed to save file from {source} to {destination}: {e}")
            return False

    async def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file asynchronously.

        Args:
            file_path (Path): Path to the file to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, file_path.unlink)
            logger.info(f"File {file_path} deleted successfully.")
            return True
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found for deletion.")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def delete_directory(self, directory_path: Path) -> bool:
        """
        Delete a directory and all its contents asynchronously.

        Args:
            directory_path (Path): Path to the directory to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, shutil.rmtree, directory_path)
            logger.info(f"Directory {directory_path} and all its contents deleted successfully.")
            return True
        except FileNotFoundError:
            logger.warning(f"Directory {directory_path} not found for deletion.")
            return False
        except Exception as e:
            logger.error(f"Failed to delete directory {directory_path}: {e}")
            return False
```

**Key Features:**

- **Asynchronous Operations**: Ensures file operations do not block the event loop.
- **Comprehensive File Management**: Handles both files and directories.
- **Error Handling**: Logs and manages exceptions during file operations.

---

### **3.7 `bot/handlers.py`**

Manages all Telegram bot interactions, including commands, button callbacks, and conversational flows. **This is the most critical file, especially with the refined String Session generation process integrated via the bot interface.**

```python
# bot/handlers.py

import asyncio
import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    ParseMode
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from .config import (
    is_admin,
    get_session,
    set_session,
    config,
    save_config
)
from .logger import logger
from .checker import TelegramChecker
from .adder import TelegramAdder
from .file_handler import FileHandler

# Define unique states for ConversationHandlers
SET_APIFY_TOKEN_STATE = 1
SET_TELEGRAM_API_ID_STATE = 2
SET_TELEGRAM_API_HASH_STATE = 3
SET_TELEGRAM_STRING_SESSION_STATE = 4
SET_TARGET_CHANNEL_USERNAME_STATE = 5

BLOCK_USER_ID_STATE = 6

class BotHandlers:
    """
    A class encapsulating all the handlers for the Telegram Bot.
    """

    def __init__(self, application, checker: TelegramChecker, adder: TelegramAdder):
        """
        Initialize the BotHandlers with the application and necessary services.

        Args:
            application: Telegram bot application instance.
            checker (TelegramChecker): Instance of TelegramChecker.
            adder (TelegramAdder): Instance of TelegramAdder.
        """
        self.application = application
        self.checker = checker
        self.adder = adder
        self.file_handler = FileHandler()
        self.register_handlers()

    def register_handlers(self):
        """
        Register all handlers (commands, callbacks, message handlers).
        """

        # -------- Command Handlers --------
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel))
        self.application.add_handler(CommandHandler("status", self.status_command))

        # -------- CallbackQueryHandlers for Buttons --------
        callback_patterns = [
            "settings",
            "upload_csv",
            "add_to_channel",
            "manage_blocked",
            "export_data",
            "exit",
            "set_apify_token",
            "set_telegram_api_id",
            "set_telegram_api_hash",
            "set_string_session",
            "set_target_channel_username",
            r"^unblock_user_\d+$",
            "block_user_prompt",
            "back_to_main",
            "export_registered_users",
            "list_user_ids"
        ]

        for pattern in callback_patterns:
            self.application.add_handler(
                CallbackQueryHandler(self.button_handler, pattern=pattern)
            )

        # -------- Conversation Handlers --------
        # Handler for setting Apify API Token
        conv_handler_set_apify = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_apify_token, pattern='set_apify_token')],
            states={
                SET_APIFY_TOKEN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_apify_token)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_apify)

        # Handler for setting Telegram API ID
        conv_handler_set_api_id = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_telegram_api_id, pattern='set_telegram_api_id')],
            states={
                SET_TELEGRAM_API_ID_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_telegram_api_id)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_api_id)

        # Handler for setting Telegram API Hash
        conv_handler_set_api_hash = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_telegram_api_hash, pattern='set_telegram_api_hash')],
            states={
                SET_TELEGRAM_API_HASH_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_telegram_api_hash)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_api_hash)

        # Handler for setting String Session
        conv_handler_set_ss = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_string_session, pattern='set_string_session')],
            states={
                SET_TELEGRAM_STRING_SESSION_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_string_session)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_ss)

        # Handler for setting Target Channel Username
        conv_handler_set_channel = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_target_channel_username, pattern='set_target_channel_username')],
            states={
                SET_TARGET_CHANNEL_USERNAME_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_target_channel_username)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_channel)

        # Handler for blocking a user
        conv_handler_block_user = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.block_user_prompt, pattern='block_user_prompt')],
            states={
                BLOCK_USER_ID_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.block_user_input_handler)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_block_user)

        # -------- Message Handlers --------
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.upload_csv_handler))

        # Register the general text message handler (if needed)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_messages))

        # -------- Error Handler --------
        self.application.add_error_handler(self.error_handler)

    def get_main_menu_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """
        Returns the main menu keyboard layout.

        Returns:
            List[List[InlineKeyboardButton]]: Keyboard layout.
        """
        return [
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
            [InlineKeyboardButton("📂 آپلود مخاطبین CSV", callback_data="upload_csv")],
            [InlineKeyboardButton("➕ افزودن کاربران به کانال هدف", callback_data="add_to_channel")],
            [InlineKeyboardButton("🛑 مدیریت کاربران مسدود شده", callback_data="manage_blocked")],
            [InlineKeyboardButton("📤 صادرات داده‌ها", callback_data="export_data")],
            [InlineKeyboardButton("❌ خروج کامل", callback_data="exit")]
        ]

    def initialize_components(self):
        """
        Reinitialize checker and adder after configuration changes.
        """
        # Reinitialize TelegramChecker
        apify_api_token = config.get("apify_api_token")
        if apify_api_token:
            self.checker = TelegramChecker(apify_api_token)
            logger.info("TelegramChecker re-initialized with new Apify API Token.")
        else:
            self.checker = None
            logger.warning("TelegramChecker not initialized. Missing Apify API Token.")

        # Reinitialize TelegramAdder
        telegram_api_id = config.get("telegram_api_id")
        telegram_api_hash = config.get("telegram_api_hash")
        telegram_string_session = config.get("telegram_string_session")
        target_channel_username = config.get("target_channel_username")
        
        if all([telegram_api_id, telegram_api_hash, telegram_string_session, target_channel_username]):
            self.adder = TelegramAdder(
                api_id=int(telegram_api_id),
                api_hash=telegram_api_hash,
                string_session=telegram_string_session,
                target_channel_username=target_channel_username
            )
            logger.info("TelegramAdder re-initialized with new Telegram credentials.")
        else:
            self.adder = None
            logger.warning("TelegramAdder not initialized. Missing Telegram credentials.")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Show the main menu keyboard
        keyboard = self.get_main_menu_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "سلام! لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /help command.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        help_text = (
            "📄 **دستورات و گزینه‌ها:**\n\n"
            "/start - شروع ربات و نمایش گزینه‌ها\n"
            "/help - نمایش پیام راهنما\n"
            "/cancel - لغو عملیات جاری\n"
            "/status - نمایش وضعیت فعلی ربات\n\n"
            "**گزینه‌ها (از طریق دکمه‌ها):**\n"
            "• ⚙️ تنظیمات\n"
            "• 📂 آپلود مخاطبین CSV\n"
            "• ➕ افزودن کاربران به کانال هدف\n"
            "• 🛑 مدیریت کاربران مسدود شده\n"
            "• 📤 صادرات داده‌ها\n"
            "• ❌ خروج کامل\n\n"
            "**نکات:**\n"
            "- فایل‌های CSV باید حاوی شماره تلفن‌ها در فرمت بین‌المللی (مثلاً +1234567890) باشند.\n"
            "- فقط کاربرانی که در لیست ادمین‌ها هستند می‌توانند از این ربات استفاده کنند.\n"
            "- پس از آپلود CSV و پردازش، می‌توانید کاربران ثبت‌شده را به کانال هدف اضافه کنید."
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /status command to display current bot configurations.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        status_text = (
            f"📊 **وضعیت ربات:**\n\n"
            f"• **Apify API Token:** {'✅ تنظیم شده' if config.get('apify_api_token') else '❌ تنظیم نشده'}\n"
            f"• **Telegram API ID:** {config.get('telegram_api_id') or '❌ تنظیم نشده'}\n"
            f"• **Telegram API Hash:** {config.get('telegram_api_hash') or '❌ تنظیم نشده'}\n"
            f"• **String Session:** {'✅ تنظیم شده' if config.get('telegram_string_session') else '❌ تنظیم نشده'}\n"
            f"• **Target Channel Username:** {config.get('target_channel_username') or '❌ تنظیم نشده'}\n"
            f"• **Blocked Users Count:** {len(config.get('blocked_users', []))}"
        )
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /cancel command to cancel ongoing operations.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        if update.message:
            await update.message.reply_text('📴 عملیات جاری لغو شد.')
        elif update.callback_query:
            await update.callback_query.edit_message_text('📴 عملیات جاری لغو شد.')
        # Clear any user data state
        context.user_data.clear()
        # Show main menu again
        keyboard = self.get_main_menu_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text(
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=reply_markup
            )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle all callback queries from inline buttons.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        data = query.data

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await query.edit_message_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Settings Menu
        if data == "settings":
            await self.settings_menu(update, context)

        elif data == "upload_csv":
            if not self.checker:
                await query.edit_message_text("❌ لطفاً ابتدا در تنظیمات ربات Apify API Token را تنظیم کنید.")
                return
            await query.edit_message_text("📂 لطفاً فایل CSV حاوی شماره تلفن‌ها را ارسال کنید.")

        elif data == "add_to_channel":
            # Check if CSV has been uploaded and processed
            session_data = get_session(user_id)
            if not session_data.get("results"):
                await query.edit_message_text(
                    "❌ لطفاً ابتدا یک فایل CSV آپلود و پردازش کنید."
                )
                return
            await self.add_to_channel(update, context)

        elif data == "manage_blocked":
            await self.manage_blocked_menu(update, context)

        elif data == "export_data":
            await self.export_data_menu(update, context)

        elif data == "exit":
            await query.edit_message_text("❌ ربات با موفقیت متوقف شد.")
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot has been stopped gracefully.")

        elif re.match(r"^unblock_user_\d+$", data):
            try:
                target_user_id = int(data.split("_")[-1])
                await self.unblock_user(update, context, target_user_id)
            except ValueError:
                await query.edit_message_text("❌ شناسه کاربری نامعتبر است.")

        elif data == "back_to_main":
            await self.start_command(update, context)

        # Export Data Handlers
        elif data == "export_registered_users":
            await self.export_registered_users(update, context)

        elif data == "list_user_ids":
            await self.list_user_ids(update, context)

        else:
            await query.edit_message_text("❓ گزینه انتخابی نامعتبر است. لطفاً دوباره تلاش کنید.")

    async def settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the settings menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("🔧 تنظیم Apify API Token", callback_data="set_apify_token"),
             InlineKeyboardButton("🔧 تنظیم Telegram API ID", callback_data="set_telegram_api_id")],
            [InlineKeyboardButton("🔧 تنظیم Telegram API Hash", callback_data="set_telegram_api_hash"),
             InlineKeyboardButton("🔧 تنظیم String Session", callback_data="set_string_session")],
            [InlineKeyboardButton("🔧 تنظیم Target Channel Username", callback_data="set_target_channel_username")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ **تنظیمات ربات:**\n\n"
            "لطفاً یکی از تنظیمات زیر را انتخاب کنید تا مقدار آن را وارد یا به‌روزرسانی کنید:",
            reply_markup=reply_markup
        )

    async def start_set_apify_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Apify API Token.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Apify API Token**\n\n"
            "لطفاً Apify API Token خود را وارد کنید:"
        )
        return SET_APIFY_TOKEN_STATE

    async def set_apify_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Apify API Token input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_token = update.message.text.strip()
        if not api_token:
            await update.message.reply_text("❌ لطفاً یک Apify API Token معتبر وارد کنید:")
            return SET_APIFY_TOKEN_STATE

        # Basic validation (Apify tokens are typically long alphanumeric strings)
        if not isinstance(api_token, str) or len(api_token) < 20:
            await update.message.reply_text("❌ لطفاً یک Apify API Token معتبر وارد کنید:")
            return SET_APIFY_TOKEN_STATE

        config["apify_api_token"] = api_token
        save_config()

        # Initialize or reinitialize TelegramChecker
        self.checker = TelegramChecker(api_token)
        logger.info("TelegramChecker re-initialized with new Apify API Token.")

        await update.message.reply_text("✅ Apify API Token با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_telegram_api_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Telegram API ID.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Telegram API ID**\n\n"
            "لطفاً Telegram API ID خود را وارد کنید (عدد):"
        )
        return SET_TELEGRAM_API_ID_STATE

    async def set_telegram_api_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Telegram API ID input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_id_text = update.message.text.strip()
        if not api_id_text.isdigit():
            await update.message.reply_text("❌ لطفاً یک Telegram API ID معتبر (عدد) وارد کنید:")
            return SET_TELEGRAM_API_ID_STATE

        api_id = int(api_id_text)
        config["telegram_api_id"] = api_id
        save_config()

        await update.message.reply_text("✅ Telegram API ID با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_telegram_api_hash(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Telegram API Hash.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Telegram API Hash**\n\n"
            "لطفاً Telegram API Hash خود را وارد کنید:"
        )
        return SET_TELEGRAM_API_HASH_STATE

    async def set_telegram_api_hash(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Telegram API Hash input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_hash = update.message.text.strip()
        if not api_hash:
            await update.message.reply_text("❌ لطفاً یک Telegram API Hash معتبر وارد کنید:")
            return SET_TELEGRAM_API_HASH_STATE

        config["telegram_api_hash"] = api_hash
        save_config()

        await update.message.reply_text("✅ Telegram API Hash با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_string_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set String Session.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم/به‌روزرسانی String Session**\n\n"
            "لطفاً String Session خود را ارسال کنید:\n"
            "📝 **توجه:** String Session حاوی اطلاعات حساس است. آن را با هیچ‌کس به اشتراک نگذارید."
        )
        return SET_TELEGRAM_STRING_SESSION_STATE

    async def set_string_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle String Session input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        string_session = update.message.text.strip()
        if not string_session:
            await update.message.reply_text("❌ لطفاً یک String Session معتبر ارسال کنید:")
            return SET_TELEGRAM_STRING_SESSION_STATE

        # Validate the String Session by attempting to connect
        api_id = config.get("telegram_api_id")
        api_hash = config.get("telegram_api_hash")
        if not all([api_id, api_hash]):
            await update.message.reply_text("❌ API ID و API Hash تنظیم نشده‌اند. لطفاً ابتدا آن‌ها را تنظیم کنید.")
            return ConversationHandler.END

        try:
            # Attempt to connect with the new String Session
            test_adder = TelegramAdder(
                api_id=int(api_id),
                api_hash=api_hash,
                string_session=string_session,
                target_channel_username=config.get("target_channel_username") or "@yourchannelusername"
            )
            await test_adder.connect()
            await test_adder.disconnect()

            # If successful, update the config
            config["telegram_string_session"] = string_session
            save_config()
            await update.message.reply_text("✅ **String Session با موفقیت تنظیم شد!**")

            # Reinitialize TelegramAdder with the new String Session
            self.initialize_components()
            return ConversationHandler.END

        except errors.RPCError as e:
            logger.error(f"Telethon connection error with new String Session: {e}")
            await update.message.reply_text(f"❌ خطا در احراز هویت با String Session جدید: {e}")
            return SET_TELEGRAM_STRING_SESSION_STATE
        except Exception as e:
            logger.error(f"Unexpected error during String Session validation: {e}")
            await update.message.reply_text("❌ خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید.")
            return SET_TELEGRAM_STRING_SESSION_STATE

    async def start_set_target_channel_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Target Channel Username.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Target Channel Username**\n\n"
            "لطفاً نام کاربری کانال هدف خود را وارد کنید (با @ شروع کنید، مثلاً @yourchannelusername):",
            parse_mode=ParseMode.MARKDOWN
        )
        return SET_TARGET_CHANNEL_USERNAME_STATE

    async def set_target_channel_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle setting the target channel username.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        text = update.message.text.strip()
        USERNAME_REGEX = re.compile(r'^@[\w]{5,32}$')  # Telegram usernames are between 5-32 characters and can include underscores

        if not USERNAME_REGEX.match(text):
            await update.message.reply_text("❌ لطفاً یک نام کاربری کانال معتبر وارد کنید (با @ شروع و بین 5 تا 32 کاراکتر):")
            return SET_TARGET_CHANNEL_USERNAME_STATE  # Reuse the same state

        config["target_channel_username"] = text
        save_config()
        await update.message.reply_text("✅ نام کاربری کانال هدف با موفقیت تنظیم شد.")
        # Reinitialize TelegramAdder with new channel
        self.initialize_components()
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def upload_csv_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle CSV file uploads.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        if update.message.document:
            file = update.message.document
            if not file.file_name.lower().endswith(".csv"):
                await update.message.reply_text("❌ لطفاً یک فایل CSV معتبر ارسال کنید.")
                return

            try:
                # Define a temporary path to save the file
                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / f"{user_id}_{file.file_name}"

                # Download the file asynchronously
                await file.get_file().download_to_drive(custom_path=str(temp_file_path))
                await update.message.reply_text("🔄 در حال پردازش فایل CSV شما. لطفاً صبر کنید...")

                # Read phone numbers from CSV asynchronously
                loop = asyncio.get_running_loop()
                if not self.checker:
                    await update.message.reply_text("❌ Apify API Token تنظیم نشده است. لطفاً در تنظیمات آن را تنظیم کنید.")
                    return

                phone_numbers = await loop.run_in_executor(None, self.checker.read_csv, str(temp_file_path))
                if not phone_numbers:
                    await update.message.reply_text("❌ فایل CSV خالی یا نامعتبر است.")
                    return

                MAX_PHONE_NUMBERS = 1000  # Adjust as needed
                if len(phone_numbers) > MAX_PHONE_NUMBERS:
                    await update.message.reply_text(f"❌ تعداد شماره تلفن‌ها بیش از حد مجاز ({MAX_PHONE_NUMBERS}) است.")
                    return

                # Check Telegram status using Apify
                results = await loop.run_in_executor(None, self.checker.check_telegram_status, phone_numbers)

                # Save results in session
                session = get_session(user_id)
                session["results"] = results
                set_session(user_id, session)

                # Save results to CSV asynchronously
                result_file = Path(f"telegram_results_{user_id}.csv")
                await loop.run_in_executor(None, self.checker.save_results, results, str(result_file))

                # Prepare a summary
                total = len(results)
                registered = len([r for r in results if r.get("isRegistered")])
                not_registered = total - registered
                summary = (
                    f"✅ **پردازش کامل شد!**\n\n"
                    f"کل شماره‌ها: {total}\n"
                    f"ثبت‌شده در تلگرام: {registered}\n"
                    f"ثبت‌نشده: {not_registered}"
                )

                # Send summary and the results file
                await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN)
                await update.message.reply_document(
                    document=InputFile(str(result_file)),
                    filename=result_file.name,
                    caption="📁 این نتایج بررسی شماره تلفن‌های شما است."
                )

                # Clean up temporary files asynchronously
                try:
                    await self.file_handler.delete_file(temp_file_path)
                    await self.file_handler.delete_file(result_file)
                    if not any(temp_dir.iterdir()):
                        await self.file_handler.delete_directory(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary files: {e}")

            except Exception as e:
                logger.error(f"Error processing CSV: {e}")
                await update.message.reply_text("❌ هنگام پردازش فایل CSV خطایی رخ داد.")
        else:
            await update.message.reply_text("❌ لطفاً یک فایل CSV ارسال کنید.")

    async def add_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Add verified users to the target channel.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.edit_message_text("🔄 در حال افزودن کاربران به کانال هدف. لطفاً صبر کنید...")

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])

        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای افزودن وجود ندارد.")
            return

        # Filter registered users with valid user IDs
        registered_users = [r for r in results if r.get("isRegistered") and r.get("userId")]
        if not registered_users:
            await query.edit_message_text("❌ هیچ شماره تلفنی ثبت‌شده در تلگرام یافت نشد.")
            return

        # Get blocked users
        blocked_users = config.get("blocked_users", [])

        # Extract user IDs
        user_ids = [r.get("userId") for r in registered_users if r.get("userId")]

        # Initialize TelegramAdder client
        if not self.adder:
            await query.edit_message_text("❌ ربات به درستی تنظیم نشده است. لطفاً با مدیر تماس بگیرید.")
            return

        try:
            await self.adder.connect()
        except errors.RPCError as e:
            logger.error(f"Telethon connection error: {e}")
            await query.edit_message_text("❌ خطا در اتصال به Telegram. لطفاً بررسی کنید.")
            return
        except Exception as e:
            logger.error(f"Unexpected error during Telethon connection: {e}")
            await query.edit_message_text("❌ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید.")
            return

        # Add users to channel
        try:
            summary = await self.adder.add_users_to_channel(user_ids, blocked_users)
        except errors.FloodWaitError as e:
            logger.warning(f"Flood wait error: {e}. Sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            await query.edit_message_text("❌ ربات در حال حاضر با محدودیت سرعت مواجه شده است. لطفاً بعداً دوباره تلاش کنید.")
            return
        except PermissionError as e:
            logger.error(f"Permission error: {e}")
            await query.edit_message_text(f"❌ {e}")
            return
        except Exception as e:
            logger.error(f"Error adding users to channel: {e}")
            await query.edit_message_text(f"❌ خطایی رخ داد: {e}")
            return
        finally:
            await self.adder.disconnect()

        # Prepare a summary message
        success_count = len(summary["added"])
        failure_count = len(summary["failed"])
        summary_message = (
            f"✅ **افزودن کاربران به کانال کامل شد!**\n\n"
            f"تعداد موفق: {success_count}\n"
            f"تعداد ناموفق: {failure_count}"
        )
        await query.edit_message_text(summary_message, parse_mode=ParseMode.MARKDOWN)

        if summary["added"]:
            added_list = ", ".join(map(str, summary["added"]))
            await query.message.reply_text(f"🟢 **کاربران اضافه شده:**\n{added_list}")

        if summary["failed"]:
            failed_list = ", ".join(map(str, summary["failed"]))
            await query.message.reply_text(f"🔴 **کاربران اضافه نشده:**\n{failed_list}")

    async def manage_blocked_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the manage blocked users menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        blocked_users = config.get("blocked_users", [])
        if not blocked_users:
            blocked_text = "🛑 **لیست کاربران مسدود شده خالی است.**"
        else:
            blocked_text = (
                "🛑 **لیست کاربران مسدود شده:**\n\n"
                + "\n".join([f"• {uid}" for uid in blocked_users])
            )

        keyboard = [
            [InlineKeyboardButton("➕ مسدود کردن کاربر جدید", callback_data="block_user_prompt")]
        ]
        # Dynamically add unblock buttons
        for uid in blocked_users:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔓 بازگشایی مسدودیت کاربر {uid}",
                    callback_data=f"unblock_user_{uid}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(blocked_text, reply_markup=reply_markup)

    async def block_user_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Prompt admin to enter a user ID to block.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "➕ لطفاً شناسه کاربری تلگرام کاربری که می‌خواهید مسدود کنید را وارد کنید (عدد):"
        )
        return BLOCK_USER_ID_STATE

    async def block_user_input_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle input for blocking a new user.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        target_user_id_text = update.message.text.strip()
        if not target_user_id_text.isdigit():
            await update.message.reply_text(
                "❌ لطفاً یک شناسه کاربری تلگرام معتبر (عدد) وارد کنید:"
            )
            return BLOCK_USER_ID_STATE

        target_user_id = int(target_user_id_text)

        if target_user_id in config.get("blocked_users", []):
            await update.message.reply_text(
                f"🔍 کاربر با شناسه {target_user_id} قبلاً مسدود شده است."
            )
        else:
            config.setdefault("blocked_users", []).append(target_user_id)
            save_config()
            await update.message.reply_text(
                f"✅ کاربر با شناسه {target_user_id} با موفقیت مسدود شد."
            )

        # Return to manage blocked menu
        await self.manage_blocked_menu(update, context)
        return ConversationHandler.END

    async def unblock_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """
        Unblock a user.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
            target_user_id (int): Telegram user ID to unblock.
        """
        user_id = update.effective_user.id
        blocked_users = config.get("blocked_users", [])

        if target_user_id in blocked_users:
            blocked_users.remove(target_user_id)
            config["blocked_users"] = blocked_users
            save_config()
            await update.callback_query.edit_message_text(
                f"✅ کاربر با شناسه {target_user_id} از لیست مسدود شده‌ها حذف شد."
            )
        else:
            await update.callback_query.edit_message_text(
                f"🔍 کاربر با شناسه {target_user_id} در لیست مسدود شده‌ها یافت نشد."
            )

        await self.manage_blocked_menu(update, context)

    async def export_data_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the export data menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await query.edit_message_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        keyboard = [
            [InlineKeyboardButton("📥 صادرات لیست کاربران ثبت‌شده", callback_data="export_registered_users")],
            [InlineKeyboardButton("🔢 لیست شناسه‌های کاربران ثبت‌شده", callback_data="list_user_ids")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📤 لطفاً گزینه مورد نظر برای صادرات داده‌ها را انتخاب کنید:",
            reply_markup=reply_markup
        )

    async def export_registered_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Export the list of registered users as a JSON file.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])
        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای صادرات وجود ندارد.")
            return

        registered_users = [r for r in results if r.get("isRegistered") and r.get("userId")]
        if not registered_users:
            await query.edit_message_text("❌ هیچ کاربر ثبت‌شده‌ای یافت نشد.")
            return

        # Save to JSON asynchronously
        output_file = Path(f"registered_users_{user_id}.json")
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: json.dump(
                    registered_users,
                    output_file.open("w", encoding="utf-8"),
                    indent=4,
                    ensure_ascii=False
                )
            )
            logger.info(f"Registered users exported to {output_file}.")
        except Exception as e:
            logger.error(f"Failed to export registered users: {e}")
            await query.edit_message_text("❌ خطایی در هنگام صادرات داده‌ها رخ داد.")
            return

        await query.edit_message_text("📤 در حال ارسال فایل صادرات...")
        await query.message.reply_document(
            document=InputFile(str(output_file)),
            filename=output_file.name,
            caption="📁 لیست کاربران ثبت‌شده"
        )

        # Clean up the exported file asynchronously
        try:
            await self.file_handler.delete_file(output_file)
        except Exception as e:
            logger.warning(f"Failed to delete exported file {output_file}: {e}")

    async def list_user_ids(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        List all user IDs processed.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])
        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای نمایش وجود ندارد.")
            return

        user_ids = [str(r.get("userId")) for r in results if r.get("isRegistered") and r.get("userId")]
        if not user_ids:
            user_ids_str = "هیچ کاربری ثبت نشده است."
        else:
            user_ids_str = ", ".join(user_ids)

        await query.edit_message_text(f"🔢 **لیست شناسه‌های کاربران ثبت‌شده:**\n{user_ids_str}")

    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle general text messages based on user state.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Other text messages can be handled as needed
        await update.message.reply_text(
            "❓ لطفاً از دکمه‌های ارائه شده استفاده کنید یا یک دستور معتبر ارسال کنید."
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Log the error and send a message to the user.

        Args:
            update (object): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_user:
            try:
                await update.effective_message.reply_text(
                    "❌ متاسفانه یک خطا رخ داد. لطفاً دوباره تلاش کنید."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
```

**Key Enhancements:**

1. **Integrated Settings for Sensitive Data:**
    - **Buttons Added:** Options to set Apify API Token, Telegram API ID, Telegram API Hash, String Session, and Target Channel Username via inline keyboard buttons.
    - **Conversation Handlers:** Implemented separate conversation handlers for each configuration setting, ensuring a smooth and secure setup process.
    - **Validation:** Each input is validated to ensure correctness before updating the configuration.

2. **Removal of Pre-filled Sensitive Data:**
    - The bot no longer relies on pre-filled sensitive data in the `.env` file. Instead, admins input all necessary configurations through the bot interface.

3. **Enhanced Error Handling:**
    - Provides clear feedback if configurations are missing or invalid.
    - Ensures that the bot remains operational even if some configurations are incomplete.

---

### **3.8 `bot/main.py`**

The entry point of the bot, initializing all components and starting the bot using either polling or webhook based on configuration.

```python
# bot/main.py

import asyncio
from telegram.ext import ApplicationBuilder

from .config import BOT_TOKEN, WEBHOOK_URL, USE_WEBHOOK, config
from .logger import logger
from .checker import TelegramChecker
from .adder import TelegramAdder
from .handlers import BotHandlers

async def main():
    """
    Initialize and run the Telegram bot.
    """
    # Initialize services
    apify_api_token = config.get("apify_api_token")
    telegram_api_id = config.get("telegram_api_id")
    telegram_api_hash = config.get("telegram_api_hash")
    telegram_string_session = config.get("telegram_string_session")
    target_channel_username = config.get("target_channel_username")

    # Initialize TelegramChecker if Apify API Token is set
    checker = TelegramChecker(apify_api_token) if apify_api_token else None

    # Initialize TelegramAdder if all Telegram credentials are set
    if all([telegram_api_id, telegram_api_hash, telegram_string_session, target_channel_username]):
        adder = TelegramAdder(
            api_id=int(telegram_api_id),
            api_hash=telegram_api_hash,
            string_session=telegram_string_session,
            target_channel_username=target_channel_username
        )
    else:
        adder = None
        logger.warning("TelegramAdder not initialized. Missing Telegram credentials.")

    # Initialize the Telegram application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Initialize handlers with the application and services
    bot_handlers = BotHandlers(application, checker, adder)

    # Start the bot
    await application.initialize()
    await application.start()

    if USE_WEBHOOK:
        # Run the webhook on specified port
        await application.run_webhook(
            listen="0.0.0.0",
            port=8443,
            url_path=BOT_TOKEN,
            webhook_url=WEBHOOK_URL
        )
        logger.info(f"Bot is running with webhook on port 8443 and listening for updates.")
    else:
        # Run polling
        await application.run_polling()
        logger.info("Bot is running with polling and listening for updates.")

    # Graceful shutdown
    await application.stop()
    await application.shutdown()
    logger.info("Bot has been shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
```

**Key Features:**

- **Service Initialization:** Sets up `TelegramChecker` and `TelegramAdder` based on configurations.
- **Bot Initialization:** Creates the Telegram bot application using the provided bot token.
- **Webhook or Polling:** Chooses between webhook and polling based on the `USE_WEBHOOK` flag.
- **Graceful Shutdown:** Ensures the bot shuts down cleanly, releasing all resources.

---

## **4. Unit Tests**

Unit tests ensure that critical components function as expected. Below are the tests for `TelegramChecker` and `TelegramAdder`.

### **4.1 `tests/test_checker.py`**

Tests the `TelegramChecker` class, ensuring correct behavior during CSV reading and Telegram status checking.

```python
# tests/test_checker.py

import unittest
from unittest.mock import patch, MagicMock
from bot.checker import TelegramChecker

class TestTelegramChecker(unittest.TestCase):

    def setUp(self):
        self.api_token = "test_apify_api_token"
        self.checker = TelegramChecker(self.api_token)

    @patch('bot.checker.ApifyClient')
    def test_check_telegram_status_success(self, mock_apify_client):
        # Mock ApifyClient responses
        mock_client_instance = MagicMock()
        mock_apify_client.return_value = mock_client_instance

        # Mock actor call
        mock_run = {"id": "run_id_123", "defaultDatasetId": "dataset_id_123", "status": "RUNNING"}
        mock_client_instance.actor.return_value.call.return_value = mock_run

        # Mock run().get()
        mock_run_info = {"status": "SUCCEEDED", "defaultDatasetId": "dataset_id_123"}
        mock_client_instance.run.return_value.get.return_value = mock_run_info

        # Mock dataset.iterate_items()
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = [{"phoneNumber": "+1234567890", "isRegistered": True, "userId": 111111}]
        mock_client_instance.dataset.return_value = mock_dataset

        phone_numbers = ["+1234567890"]
        results = self.checker.check_telegram_status(phone_numbers)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["phoneNumber"], "+1234567890")
        self.assertTrue(results[0]["isRegistered"])
        self.assertEqual(results[0]["userId"], 111111)

    @patch('bot.checker.open', new_callable=unittest.mock.mock_open, read_data="phone\n+1234567890\n+0987654321")
    def test_read_csv_valid(self, mock_file):
        phone_numbers = self.checker.read_csv("dummy_path.csv")
        self.assertEqual(phone_numbers, ["phone", "+1234567890", "+0987654321"])

    @patch('bot.checker.open', new_callable=unittest.mock.mock_open, read_data="")
    def test_read_csv_invalid(self, mock_file):
        phone_numbers = self.checker.read_csv("dummy_path.csv")
        self.assertEqual(phone_numbers, [])

if __name__ == '__main__':
    unittest.main()
```

**Key Features:**

- **Mocking External Dependencies:** Uses `unittest.mock` to simulate ApifyClient behavior.
- **Coverage:** Tests successful Telegram status checks and CSV reading under valid and invalid conditions.

---

### **4.2 `tests/test_adder.py`**

Tests the `TelegramAdder` class, ensuring correct behavior during user addition to channels and handling various Telethon exceptions.

```python
# tests/test_adder.py

import unittest
from unittest.mock import patch, MagicMock
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, UserAlreadyParticipantError, ChatWriteForbiddenError
from bot.adder import TelegramAdder
from telethon import functions

class TestTelegramAdder(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.api_id = 123456
        self.api_hash = "test_api_hash"
        self.string_session = "test_string_session"
        self.target_channel_username = "@testchannel"
        self.adder = TelegramAdder(
            api_id=self.api_id,
            api_hash=self.api_hash,
            string_session=self.string_session,
            target_channel_username=self.target_channel_username
        )

    @patch('bot.adder.TelegramClient')
    async def test_add_users_to_channel_success(self, mock_telethon_client):
        mock_client_instance = MagicMock()
        mock_telethon_client.return_value = mock_client_instance

        # Mock get_entity
        mock_client_instance.get_entity.return_value = MagicMock()

        # Mock InviteToChannelRequest
        mock_client_instance(functions.channels.InviteToChannelRequest).return_value = MagicMock()

        user_ids = [111111, 222222]
        blocked_users = []
        summary = await self.adder.add_users_to_channel(user_ids, blocked_users)

        self.assertEqual(summary["added"], user_ids)
        self.assertEqual(summary["failed"], [])

    @patch('bot.adder.TelegramClient')
    async def test_add_users_to_channel_flood_wait(self, mock_telethon_client):
        mock_client_instance = MagicMock()
        mock_telethon_client.return_value = mock_client_instance

        # Mock get_entity
        mock_client_instance.get_entity.return_value = MagicMock()

        # Mock InviteToChannelRequest to raise FloodWaitError for first user
        async def mock_invite(*args, **kwargs):
            if args[0].users[0].id == 111111:
                raise FloodWaitError(seconds=60)
            return MagicMock()

        mock_client_instance(functions.channels.InviteToChannelRequest).side_effect = mock_invite

        user_ids = [111111, 222222]
        blocked_users = []
        summary = await self.adder.add_users_to_channel(user_ids, blocked_users)

        self.assertEqual(summary["added"], [222222])
        self.assertEqual(summary["failed"], [111111])

    @patch('bot.adder.TelegramClient')
    async def test_add_users_to_channel_user_privacy_restricted(self, mock_telethon_client):
        mock_client_instance = MagicMock()
        mock_telethon_client.return_value = mock_client_instance

        # Mock get_entity
        mock_client_instance.get_entity.return_value = MagicMock()

        # Mock InviteToChannelRequest to raise UserPrivacyRestrictedError
        async def mock_invite(*args, **kwargs):
            raise UserPrivacyRestrictedError()

        mock_client_instance(functions.channels.InviteToChannelRequest).side_effect = mock_invite

        user_ids = [333333]
        blocked_users = []
        summary = await self.adder.add_users_to_channel(user_ids, blocked_users)

        self.assertEqual(summary["added"], [])
        self.assertEqual(summary["failed"], [333333])

    @patch('bot.adder.TelegramClient')
    async def test_add_users_to_channel_user_already_participant(self, mock_telethon_client):
        mock_client_instance = MagicMock()
        mock_telethon_client.return_value = mock_client_instance

        # Mock get_entity
        mock_client_instance.get_entity.return_value = MagicMock()

        # Mock InviteToChannelRequest to raise UserAlreadyParticipantError
        async def mock_invite(*args, **kwargs):
            raise UserAlreadyParticipantError()

        mock_client_instance(functions.channels.InviteToChannelRequest).side_effect = mock_invite

        user_ids = [444444]
        blocked_users = []
        summary = await self.adder.add_users_to_channel(user_ids, blocked_users)

        self.assertEqual(summary["added"], [])
        self.assertEqual(summary["failed"], [444444])

    @patch('bot.adder.TelegramClient')
    async def test_add_users_to_channel_chat_write_forbidden(self, mock_telethon_client):
        mock_client_instance = MagicMock()
        mock_telethon_client.return_value = mock_client_instance

        # Mock get_entity
        mock_client_instance.get_entity.return_value = MagicMock()

        # Mock InviteToChannelRequest to raise ChatWriteForbiddenError
        async def mock_invite(*args, **kwargs):
            raise ChatWriteForbiddenError()

        mock_client_instance(functions.channels.InviteToChannelRequest).side_effect = mock_invite

        user_ids = [555555]
        blocked_users = []
        summary = await self.adder.add_users_to_channel(user_ids, blocked_users)

        self.assertEqual(summary["added"], [])
        self.assertEqual(summary["failed"], [555555])

if __name__ == '__main__':
    unittest.main()
```

**Key Features:**

- **Comprehensive Testing:** Covers successful additions and various Telethon exceptions.
- **Mocking:** Simulates Telethon's asynchronous behavior using `unittest.mock`.

---

## **5. Running the Bot**

Follow these steps to set up and run your Telegram bot:

### **5.1. Installation**

1. **Clone the Repository:**

    *(Assuming you have stored the bot's code in a repository)*

    ```bash
    git clone https://github.com/yourusername/telegram_bot.git
    cd telegram_bot
    ```

2. **Set Up Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Unix or MacOS
    venv\Scripts\activate     # On Windows
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables:**

    - Create a `.env` file in the root directory with the following content:

        ```env
        # .env

        TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        WEBHOOK_URL=https://yourdomain.com/your_bot_token_here
        ADMINS=123456789,987654321  # Comma-separated Telegram User IDs
        USE_WEBHOOK=False
        ```

    - **Replace the placeholders:**
        - **`your_telegram_bot_token_here`**: Obtain this from [BotFather](https://t.me/BotFather) on Telegram.
        - **`yourdomain.com`**: Your server's domain if using webhooks.
        - **`123456789,987654321`**: Telegram user IDs of administrators.

    **Important:** Do **NOT** include sensitive information like `APIFY_API_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_STRING_SESSION`, and `TARGET_CHANNEL_USERNAME` in the `.env` file. These will be set via the bot interface.

5. **Initialize `config.json`:**

    - Upon first run, the bot will create a `config.json` file with default configurations. Ensure this file is in the root directory.

    ```json
    {
        "blocked_users": [],
        "user_sessions": {},
        "telegram_api_id": null,
        "telegram_api_hash": null,
        "telegram_string_session": null,
        "target_channel_username": null,
        "apify_api_token": null
    }
    ```

### **5.2. Running the Bot**

1. **Activate Virtual Environment:**

    ```bash
    # On Unix or MacOS
    source venv/bin/activate

    # On Windows
    venv\Scripts\activate
    ```

2. **Start the Bot:**

    ```bash
    python bot/main.py
    ```

    - The bot will start using polling or webhook based on the `USE_WEBHOOK` flag in the `.env` file.
    - **Polling Mode:** Continuously checks for new updates.
    - **Webhook Mode:** Listens for updates at the specified `WEBHOOK_URL`.

### **5.3. Using the Bot**

1. **Interact as Admin:**

    - From one of the admin accounts specified in the `ADMINS` environment variable, send the `/start` command to the bot.

2. **Configure Essential Settings:**

    - **Settings Menu:**
        - Click on the "⚙️ تنظیمات" button to access the settings menu.
        - **Set Apify API Token:**
            - Click on "🔧 تنظیم Apify API Token" and follow the prompts to input your Apify API Token.
        - **Set Telegram API ID:**
            - Click on "🔧 تنظیم Telegram API ID" and input your Telegram API ID.
        - **Set Telegram API Hash:**
            - Click on "🔧 تنظیم Telegram API Hash" and input your Telegram API Hash.
        - **Set String Session:**
            - Click on "🔧 تنظیم String Session" and input your Telegram String Session.
                - **Generating String Session:**
                    - If you haven't generated a String Session yet, follow the steps below.
        - **Set Target Channel Username:**
            - Click on "🔧 تنظیم Target Channel Username" and input your target channel's username (e.g., `@yourchannelusername`).

3. **Generate String Session:**

    - **Prerequisite:** Ensure that `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` are set via the bot's settings.
    - **Steps:**
        1. **Create a Script to Generate String Session:**

            ```python
            # generate_string_session.py

            from telethon import TelegramClient
            from telethon.sessions import StringSession

            api_id = YOUR_TELEGRAM_API_ID
            api_hash = 'YOUR_TELEGRAM_API_HASH'

            with TelegramClient(StringSession(), api_id, api_hash) as client:
                string_session = client.session.save()
                print(f"Your String Session: {string_session}")
            ```

            - **Replace `YOUR_TELEGRAM_API_ID` and `YOUR_TELEGRAM_API_HASH`** with your actual credentials.

        2. **Run the Script:**

            ```bash
            python generate_string_session.py
            ```

            - **Follow the Prompts:** The script will prompt you to enter your phone number and the verification code sent by Telegram.
            - **Copy the Output:** The script will output your `String Session`. **Keep this secure**.

        3. **Set the String Session via the Bot:**

            - **Start the Bot:** Ensure your bot is running (`python bot/main.py`).
            - **Interact as Admin:** From an admin account, send the `/start` command.
            - **Navigate to Settings:** Click on the "⚙️ تنظیمات" button.
            - **Set String Session:** Click on "🔧 تنظیم String Session" and paste the `String Session` obtained from the script.
            - **Confirmation:** The bot will validate and confirm the successful setup.

4. **Upload CSV File:**

    - Click on "📂 آپلود مخاطبین CSV" to upload a CSV file containing phone numbers.
    - **CSV Format:** Ensure the CSV contains phone numbers in international format (e.g., `+1234567890`).
    - **Processing:** The bot will process the CSV, check Telegram registration status via Apify, and provide a summary.

5. **Add Users to Channel:**

    - After uploading and processing the CSV, click on "➕ افزودن کاربران به کانال هدف" to add verified users to your target channel.
    - **Blocked Users:** Users listed in the blocked users list will be skipped.

6. **Manage Blocked Users:**

    - Click on "🛑 مدیریت کاربران مسدود شده" to view, add, or remove blocked users.
    - **Blocking Users:** You can block specific Telegram user IDs to prevent them from being added to the channel.

7. **Export Data:**

    - Click on "📤 صادرات داده‌ها" to export processed data.
    - **Export Options:**
        - **Export Registered Users:** Exports the list of users registered on Telegram.
        - **List User IDs:** Displays all processed Telegram user IDs.

8. **Exit the Bot:**

    - Click on "❌ خروج کامل" to stop the bot gracefully.

---

## **6. Final Steps to Ensure Functionality**

Before deploying your bot, ensure the following:

### **6.1. Secure Configurations**

- **Protect `config.json`:**
    - Ensure that `config.json` is secured and not accessible publicly.
    - **Permissions:** Set appropriate file permissions to restrict unauthorized access.

- **Protect `.env`:**
    - Ensure that the `.env` file is included in `.gitignore` to prevent accidental exposure.

- **Secure String Session:**
    - The String Session contains sensitive information. Ensure it's stored securely and never shared.

### **6.2. Verify Configurations**

1. **Check `config.json`:**

    - After setting all configurations via the bot interface, ensure that `config.json` reflects the correct values.

    ```json
    {
        "blocked_users": [],
        "user_sessions": {},
        "telegram_api_id": 123456,
        "telegram_api_hash": "your_telegram_api_hash_here",
        "telegram_string_session": "your_string_session_here",
        "target_channel_username": "@yourchannelusername",
        "apify_api_token": "your_apify_api_token_here"
    }
    ```

2. **Test Bot Functionalities:**

    - **Upload CSV:** Send a CSV file with phone numbers and verify processing.
    - **Add to Channel:** Attempt to add users to the target channel and observe the results.
    - **Manage Blocked Users:** Block and unblock users to ensure the functionality works.
    - **Export Data:** Export registered users and their IDs to verify data handling.

### **6.3. Ensure Security**

- **Restrict Admin Access:**
    - Only trusted Telegram user IDs should be listed in the `ADMINS` environment variable.

- **Handle Sensitive Data Carefully:**
    - The String Session and Apify API Token are sensitive. Ensure they are stored securely and access is restricted.

- **Monitor Logs:**
    - Regularly monitor the `logs/bot.log` file for any unusual activities or errors.

---

## **7. Conclusion**

By following this comprehensive setup, your Telegram bot should function seamlessly, offering capabilities to upload and process CSV files, manage users, interact with Telegram channels, and export data. The integrated settings for sensitive information via the bot interface enhance usability and security, eliminating the need for manual configuration steps and reducing the risk of exposing sensitive data.

**Best Practices Implemented:**

- **Modular Codebase:** Separation of concerns across different modules enhances readability and maintainability.
- **Asynchronous Operations:** Utilizes Python's `asyncio` for non-blocking operations, ensuring scalability.
- **Robust Error Handling:** Catches and logs exceptions, providing clear feedback to users.
- **Logging:** Implements structured logging with rotation to monitor bot activities and troubleshoot issues.
- **Unit Testing:** Ensures critical components behave as expected, reducing the likelihood of bugs.
- **Secure Configuration Management:** Uses environment variables and secure storage for sensitive information, preventing accidental exposure.

**Next Steps:**

- **Deployment:** Consider deploying the bot on a reliable server or cloud platform. If using webhooks, ensure your server has a valid SSL certificate.
- **Security Enhancements:** Implement additional security measures such as input validation, rate limiting, and access controls.
- **Feature Expansion:** Depending on your requirements, you can expand the bot's functionalities, integrate with databases, or add more interactive features.

Feel free to reach out if you encounter any issues or need further assistance!