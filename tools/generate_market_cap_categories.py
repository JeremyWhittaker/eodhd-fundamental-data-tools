import os
import json
import csv
import argparse
import logging
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_market_caps(data_dir: str) -> Dict[str, int]:
    """
    Extracts market capitalization data from JSON files in the specified directory.

    Args:
        data_dir (str): Path to the directory containing JSON files.

    Returns:
        Dict[str, int]: A dictionary mapping symbols to their market capitalizations.
    """
    market_caps = {}

    for json_file in Path(data_dir).glob("*.json"):
        try:
            with open(json_file, "r") as file:
                data = json.load(file)

            symbol = json_file.stem.upper()

            # Skip mutual funds
            general_data = data.get("General", {})
            if general_data.get("Type") == "FUND":
                logging.info(f"Skipping mutual fund: {symbol}")
                continue

            # Extract market capitalization
            market_cap = data.get("Highlights", {}).get("MarketCapitalization")
            if isinstance(market_cap, str):
                market_cap = int(market_cap.replace(",", ""))
            elif not isinstance(market_cap, int):
                logging.warning(f"Market cap for {symbol} is invalid. Skipping.")
                continue

            market_caps[symbol] = market_cap
        except Exception as e:
            logging.error(f"Error processing file {json_file}: {e}")

    return market_caps


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
            categories['nano'].append((symbol, cap))
        elif 50_000_000 <= cap < 300_000_000:
            categories['micro'].append((symbol, cap))
        elif 300_000_000 <= cap < 2_000_000_000:
            categories['small'].append((symbol, cap))
        elif 2_000_000_000 <= cap < 10_000_000_000:
            categories['mid'].append((symbol, cap))
        elif 10_000_000_000 <= cap < 200_000_000_000:
            categories['large'].append((symbol, cap))
        elif cap >= 200_000_000_000:
            categories['mega'].append((symbol, cap))
        else:
            categories['unknown'].append((symbol, cap))

    return categories


def write_categories_to_csv(categories: Dict[str, list], output_dir: str):
    """
    Writes categorized symbols to CSV files.

    Args:
        categories (Dict[str, list]): Market cap categories with lists of symbols.
        output_dir (str): Directory to save the CSV files.
    """
    os.makedirs(output_dir, exist_ok=True)

    for category, symbols in categories.items():
        output_file = os.path.join(output_dir, f"{category}_market_caps.csv")
        try:
            with open(output_file, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Symbol", "MarketCapitalization"])
                symbols.sort(key=lambda x: x[1], reverse=True)  # Sort by market cap descending
                writer.writerows(symbols)
            logging.info(f"Saved {category} market caps to {output_file}")
        except Exception as e:
            logging.error(f"Error writing {category} market caps to CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate market cap categories from fundamental data.")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="../data/fundamental_data/",
        help="Path to the directory containing JSON files. Default: ./data/fundamental_data/"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="../market_cap_categories/",
        help="Directory to save the categorized market cap CSV files. Default: ./market_cap_categories/"
    )
    args = parser.parse_args()

    logging.info("Starting market cap categorization...")
    market_caps = extract_market_caps(args.data_dir)
    categories = categorize_market_caps(market_caps)
    write_categories_to_csv(categories, args.output_dir)
    logging.info("Market cap categorization complete.")
