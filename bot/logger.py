# bot/logger.py
#Configures the logging mechanism, ensuring that logs are written to a file with rotation to prevent uncontrolled growth.
# bot/logger.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

# Determine the directory where the script is located
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure the logs directory exists
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Define the log file path
LOG_FILE = LOG_DIR / "bot.log"

# Configure logging with rotation to prevent log file from growing indefinitely
logger = logging.getLogger("TelegramBot")

# Allow log level to be set via environment variable
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logger.setLevel(log_level)

# File handler
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)


#Key Features:
#
#Rotating File Handler: Limits log file size to 5MB with up to 5 backups.
#Structured Logging: Includes timestamps, log levels, and messages for clarity.
#
#**Improvements:**
#
#1. **Added Console Handler:**
#   - Facilitates real-time logging during development and debugging.
#
#2. **Log Level Flexibility:**
#   - Allows setting log levels via the `.env` file, enabling more verbose logging (`DEBUG`) when needed.
#
#3. **Security:**
#   - Logs are stored in the `logs/` directory, which is excluded from version control via `.gitignore`.
#