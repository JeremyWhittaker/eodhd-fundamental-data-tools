import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def categorize_market_caps(market_caps: Dict[str, int]) -> Dict[str, list]:
    """
    Categorizes symbols into market cap categories.

    Args:
        market_caps (Dict[str, int]): A dictionary of symbols and their market caps.

    Returns:
        Dict[str, list]: A dictionary mapping market cap categories to lists of symbols.
    """
    categories = {
        'nano': [],
        'micro': [],
        'small': [],
        'mid': [],
        'large': [],
        'mega': [],
        'unknown': []
    }

    for symbol, cap in market_caps.items():
        if cap < 50_000_000:
            categories['nano'].append(symbol)
        elif 50_000_000 <= cap < 300_000_000:
            categories['micro'].append(symbol)
        elif 300_000_000 <= cap < 2_000_000_000:
            categories['small'].append(symbol)
        elif 2_000_000_000 <= cap < 10_000_000_000:
            categories['mid'].append(symbol)
        elif 10_000_000_000 <= cap < 200_000_000_000:
            categories['large'].append(symbol)
        elif cap >= 200_000_000_000:
            categories['mega'].append(symbol)
        else:
            categories['unknown'].append(symbol)

    return categories

def get_market_caps(data_dir, output_csv):
    """
    Processes all JSON files in the specified directory to extract market capitalization data.

    Args:
        data_dir (str): Path to the directory containing JSON files.
        output_csv (str): Path to the CSV file to save the results.

    Returns:
        list of tuples: A list of (symbol, market_cap) tuples sorted by market cap descending.
    """
    market_caps = []

    # Iterate through all JSON files in the directory
    for json_file in Path(data_dir).glob("*.json"):
        try:
            with open(json_file, "r") as file:
                data = json.load(file)

            # Extract the symbol from the filename
            symbol = json_file.stem.upper()

            # Check if the symbol is a mutual fund
            general_data = data.get("General", {})
            if general_data.get("Type") == "FUND":
                logging.info(f"Skipping mutual fund: {symbol}")
                continue

            # Navigate to the 'MarketCapitalization' field in 'Highlights'
            market_cap = data.get("Highlights", {}).get("MarketCapitalization")

            if market_cap:
                # Ensure the value is numeric, either as an int or from a string
                if isinstance(market_cap, str):
                    market_cap_value = int(market_cap.replace(",", ""))
                elif isinstance(market_cap, int):
                    market_cap_value = market_cap
                else:
                    logging.warning(f"Unexpected data type for market cap in {symbol}: {type(market_cap)}")
                    continue

                market_caps.append((symbol, market_cap_value))
            else:
                logging.warning(f"Market cap not found for {symbol}. Skipping.")
        except Exception as e:
            logging.error(f"Error processing file {json_file}: {e}")

    # Sort by market capitalization in descending order
    market_caps.sort(key=lambda x: x[1], reverse=True)

    # Write to CSV
    try:
        with open(output_csv, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Symbol", "MarketCapitalization"])  # Write header
            writer.writerows(market_caps)
        logging.info(f"Market capitalization data saved to {output_csv}")
    except Exception as e:
        logging.error(f"Error writing to CSV file {output_csv}: {e}")

    return market_caps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get and categorize market caps.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="../data/fundamental_data/",
        help="Directory where JSON files are located."
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="../data/market_caps.csv",
        help="CSV file to output market caps."
    )
    parser.add_argument(
        "--market-cap",
        type=str,
        required=False,
        choices=['nano', 'micro', 'small', 'mid', 'large', 'mega', 'unknown'],
        help="If provided, return a list of symbols in that market cap category."
    )

    args = parser.parse_args()

    logging.info("Starting market cap extraction...")
    market_caps_list = get_market_caps(args.data_dir, args.output_csv)
    logging.info("Market cap extraction complete.")

    # Convert list of tuples to dict for categorization
    market_caps_dict = {symbol: cap for symbol, cap in market_caps_list}
    categories = categorize_market_caps(market_caps_dict)

    if args.market_cap:
        selected_category = args.market_cap
        result = categories.get(selected_category, [])
        # Print Python-formatted list of symbols
        print(result)
