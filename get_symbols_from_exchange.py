import os
import requests
import json
import logging
from pathlib import Path
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("exchange_symbols.log"),
        logging.StreamHandler()
    ]
)

# Constants
API_KEY = os.getenv("EODHD_API_KEY")
BASE_URL = "https://eodhd.com/api"
DATA_DIR = Path("./data/exchanges")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_exchanges(api_key):
    """Fetches the list of exchanges from the EODHD API."""
    url = f"{BASE_URL}/exchanges-list/?api_token={api_key}&fmt=json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_symbols_for_exchange(api_key, exchange_code):
    """Fetches the list of symbols for a given exchange."""
    url = f"{BASE_URL}/exchange-symbol-list/{exchange_code}?api_token={api_key}&fmt=json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def save_to_json(data, filename):
    """Saves the data to a JSON file."""
    file_path = DATA_DIR / filename
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return file_path

def was_modified_today(file_path):
    """Checks if the file was modified today."""
    if not file_path.exists():
        return False
    file_mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    return file_mod_time.date() == datetime.today().date()

def main():
    try:
        # Fetch list of exchanges
        exchanges = get_exchanges(API_KEY)
        logging.info(f"Retrieved {len(exchanges)} exchanges.")

        for exchange in exchanges:
            exchange_code = exchange['Code']
            file_path = DATA_DIR / f"{exchange_code}.json"

            if was_modified_today(file_path):
                logging.info(f"File for exchange {exchange_code} was modified today; skipping download.")
                continue

            logging.info(f"Processing exchange: {exchange_code}")

            # Fetch symbols for the exchange
            symbols = get_symbols_for_exchange(API_KEY, exchange_code)
            logging.info(f"Retrieved {len(symbols)} symbols for exchange {exchange_code}.")

            # Save symbols to JSON file
            save_to_json(symbols, f"{exchange_code}.json")

            # Log head and tail of the data
            logging.debug(f"Head of {exchange_code} data:\n{symbols[:5]}")
            logging.debug(f"Tail of {exchange_code} data:\n{symbols[-5:]}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
