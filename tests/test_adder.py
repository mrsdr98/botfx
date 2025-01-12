# tests/test_adder.py

#Tests the TelegramAdder class, ensuring correct behavior during user addition to channels and handling various Telethon exceptions.

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
#Key Features:
#
#Comprehensive Testing: Covers successful additions and various Telethon exceptions.
#Mocking: Simulates Telethon's asynchronous behavior using unittest.mock.