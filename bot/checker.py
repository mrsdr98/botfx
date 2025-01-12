# bot/checker.py
#Uses the Apify service to verify if phone numbers are registered on Telegram.

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




#Key Features:
#
#Batch Processing: Processes phone numbers in batches of 10 to optimize API usage.
#Apify Integration: Utilizes Apify actors to check Telegram registration status.
#Error Handling: Robustly handles potential errors during API calls.
#Result Management: Saves and displays results in CSV format.



