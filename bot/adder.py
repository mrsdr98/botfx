# bot/adder.py

#Uses Telethon to add users to a specified Telegram channel, handling various exceptions and rate limits.



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

#Key Features:
#
#Telethon Integration: Manages connections and interactions with the Telegram API.
#Error Handling: Gracefully handles various Telethon exceptions, including rate limits.
#Rate Limiting: Implements delays to respect Telegram's rate limits.