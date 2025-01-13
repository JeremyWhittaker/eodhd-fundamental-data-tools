import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from eodhd import APIClient
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
import time
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def setup_logging():
    """
    Configures logging for the script.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sleep_for(seconds):
    """
    Sleeps for the given number of seconds.
    """
    logging.info(f"Sleeping for {seconds} seconds...")
    time.sleep(seconds)

def sleep_until_next_5am():
    """
    Sleeps until 5 AM the next day.
    """
    now = datetime.now()
    next_5am = datetime.combine(now + timedelta(days=1), datetime.min.time()) + timedelta(hours=5)
    sleep_seconds = (next_5am - now).total_seconds()
    logging.info(f"Processing complete. Sleeping until {next_5am.strftime('%Y-%m-%d %H:%M:%S')} ({int(sleep_seconds)} seconds).")
    time.sleep(sleep_seconds)

def fetch_fundamental_data(api_client, ticker):
    """
    Fetches fundamental data for the given ticker using the EODHD API client.

    Returns:
        dict: The fundamental data if successful; otherwise, None.
    """
    try:
        data = api_client.get_fundamentals_data(ticker)

        if not data:
            logging.error(f"No data returned for {ticker}. Skipping to next symbol.")
            return None

        if isinstance(data, dict):
            return data
        else:
            logging.error(f"Invalid data format returned for {ticker}. Skipping to next symbol.")
            return None

    except Exception as e:
        logging.error(f"Unexpected error for {ticker}: {e}")
        return None

def save_json(data, filepath):
    """
    Saves JSON data to a file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)
    logging.debug(f"Saved JSON to {filepath}")

def file_modified_within_days(filepath, days):
    """
    Checks if a file was modified within the last 'days' days.
    """
    if not os.path.exists(filepath):
        return False
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - file_mod_time < timedelta(days=days)

def load_symbols_from_country_file(filepath, exchange=None):
    """
    Loads symbols from the specified country JSON file and filters by exchange if specified.
    """
    if not Path(filepath).exists():
        logging.error(f"File {filepath} not found.")
        return {}

    with open(filepath, "r") as file:
        data = json.load(file)

    symbols_by_exchange = {}
    for entry in data:
        exchange_code = entry.get("Exchange")
        symbol = entry.get("Code")
        if exchange_code and symbol:
            symbols_by_exchange.setdefault(exchange_code, []).append(symbol)

    if exchange:
        return symbols_by_exchange.get(exchange, [])
    return symbols_by_exchange

if __name__ == "__main__":
    setup_logging()

    api_key = os.getenv("EODHD_API_KEY")
    if not api_key:
        logging.error("EODHD API key not found. Please set it in the .env file.")
        exit(1)

    # Argument parsing
    parser = argparse.ArgumentParser(description="Fetch and save fundamental data for stock tickers.")
    parser.add_argument("--country", type=str, required=True, help="Country code (e.g., 'US').")
    parser.add_argument("--exchange", type=str, help="Exchange code to fetch symbols from (optional).")
    parser.add_argument("--output_dir", default="./data/fundamental_data", help="Directory to save JSON files.")
    parser.add_argument("--days", type=int, default=10, help="Number of days to check for file modification.")
    parser.add_argument("--errors_before_sleep", type=int, default=50, help="Number of errors to process before sleeping.")
    parser.add_argument("--sleep_time", type=int, default=3600, help="Time to sleep in seconds after processing a batch of errors.")
    args = parser.parse_args()

    country_file = Path(f"./data/exchanges/{args.country.upper()}.json")

    symbols = load_symbols_from_country_file(country_file, args.exchange)
    if not symbols:
        logging.error(f"No symbols found for country '{args.country}' or exchange '{args.exchange}'.")
        sleep_until_next_5am()
        exit(1)

    if not args.exchange:
        prioritized_exchanges = ["NYSE ARCA", "NASDAQ", "NYSE", "AMEX", "ARCA"]
        prioritized_symbols = []
        for exch in prioritized_exchanges:
            if exch in symbols:
                prioritized_symbols.extend(symbols.pop(exch))
        for remaining_symbols in symbols.values():
            prioritized_symbols.extend(remaining_symbols)
        symbols = prioritized_symbols

    api_client = APIClient(api_key)

    error_count = 0  # Tracks errors

    while True:  # Loop to ensure continuous execution
        try:
            for symbol in tqdm(symbols, desc="Fetching data"):
                output_filepath = os.path.join(args.output_dir, f"{symbol.lower()}.json")

                if file_modified_within_days(output_filepath, args.days):
                    # Skip recent files and log as DEBUG
                    logging.debug(f"Data for {symbol} is recent; skipping re-download.")
                    continue

                logging.debug(f"Fetching data for {symbol}...")
                data = fetch_fundamental_data(api_client, symbol)

                if data:
                    save_json(data, output_filepath)
                    # Log successful saves as DEBUG
                    logging.debug(f"Data for {symbol} saved successfully.")
                else:
                    # Increment error count only on actual errors
                    error_count += 1
                    logging.warning(f"Failed to fetch data for {symbol}. Error count: {error_count}")

                # Sleep after reaching the error threshold
                if error_count >= args.errors_before_sleep:
                    logging.warning(f"Reached {error_count} errors. Sleeping for {args.sleep_time} seconds.")
                    sleep_for(args.sleep_time)
                    error_count = 0  # Reset error count after sleep

            # Once all symbols are processed, sleep until the next 5 AM
            sleep_until_next_5am()

        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            sleep_until_next_5am()
