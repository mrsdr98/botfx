# tests/test_checker.py
#Tests the TelegramChecker class, ensuring correct behavior during CSV reading and Telegram status checking.


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



#Key Features:
#
#Mocking External Dependencies: Uses unittest.mock to simulate ApifyClient behavior.
#Coverage: Tests successful Telegram status checks and CSV reading under valid and invalid conditions.