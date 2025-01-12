# bot/logger.py
#Configures the logging mechanism, ensuring that logs are written to a file with rotation to prevent uncontrolled growth.
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



#Key Features:
#
#Rotating File Handler: Limits log file size to 5MB with up to 5 backups.
#Structured Logging: Includes timestamps, log levels, and messages for clarity.
