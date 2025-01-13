# bot/file_handler.py
#Manages file operations such as saving, deleting files, and handling directories asynchronously.


import asyncio
from pathlib import Path
from typing import Union
import shutil
import aiofiles
import aiofiles.os

from .logger import logger

class FileHandler:
    """
    A class to handle asynchronous file operations.
    """

    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Asynchronously delete a file.

        Args:
            file_path (str | Path): Path to the file to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                await aiofiles.os.remove(str(path))
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def delete_directory(self, dir_path: Union[str, Path]) -> bool:
        """
        Asynchronously delete a directory.

        Args:
            dir_path (str | Path): Path to the directory to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                await asyncio.to_thread(shutil.rmtree, path)
                logger.info(f"Deleted directory: {dir_path}")
                return True
            else:
                logger.warning(f"Directory not found for deletion: {dir_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")
            return False



#Key Features:
#
#Asynchronous Operations: Ensures file operations do not block the event loop.
#Comprehensive File Management: Handles both files and directories.
#Error Handling: Logs and manages exceptions during file operations.

#**Improvements:**
#
#1. **Truly Asynchronous Operations:**
#   - Utilizes `aiofiles` for non-blocking file deletion.
#   - Employs `asyncio.to_thread` for operations like `shutil.rmtree` that aren't inherently asynchronous.
#
#2. **Error Handling Enhancements:**
#   - Comprehensive exception handling with detailed logging.
#
#3. **Performance Optimizations:**
#   - Efficiently handles file and directory deletions without blocking the event loop.
#
#4. **Documentation:**
#   - Added docstrings for clarity and maintainability.



