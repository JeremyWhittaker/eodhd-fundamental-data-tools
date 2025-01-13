import json
import argparse
from pathlib import Path

def list_unique_exchanges_by_country(data_dir, country_code):
    """
    Reads a JSON file for the specified country and prints a list of all unique exchanges.

    Args:
        data_dir (str): Path to the directory containing JSON files for different countries.
        country_code (str): The country code (e.g., 'US', 'us') to specify the JSON file to read.
    """
    # Construct possible file paths
    upper_case_file = Path(data_dir) / f"{country_code.upper()}.json"
    lower_case_file = Path(data_dir) / f"{country_code.lower()}.json"

    # Determine which file exists
    if upper_case_file.exists():
        json_file_path = upper_case_file
    elif lower_case_file.exists():
        json_file_path = lower_case_file
    else:
        print(f"File for country code '{country_code}' not found. Tried: {upper_case_file}, {lower_case_file}")
        return

    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Extract the 'Exchange' field and get unique values
        exchanges = {entry.get("Exchange") for entry in data if "Exchange" in entry}

        print(f"Unique Exchanges in {country_code.upper()}:")
        for exchange in sorted(exchanges):  # Sort for easier readability
            print(exchange)

    except json.JSONDecodeError:
        print(f"Error decoding JSON in file {json_file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List unique exchanges for a specific country.")
    parser.add_argument("--country", type=str, required=True, help="Country code to specify the JSON file (e.g., 'US', 'us').")
    parser.add_argument("--data_dir", type=str, default="./data/exchanges", help="Path to the directory containing JSON files.")
    args = parser.parse_args()

    list_unique_exchanges_by_country(args.data_dir, args.country)
