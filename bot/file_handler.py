# bot/file_handler.py
#Manages file operations such as saving, deleting files, and handling directories asynchronously.


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




#Key Features:
#
#Asynchronous Operations: Ensures file operations do not block the event loop.
#Comprehensive File Management: Handles both files and directories.
#Error Handling: Logs and manages exceptions during file operations.
