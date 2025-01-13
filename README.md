# EODHD Fundamentals Helper

A Python-based toolkit for interacting with the EODHD API to fetch, organize, and analyze fundamental financial data. This repository includes utilities to retrieve exchange symbols, download fundamental data, and generate structured outputs for analysis or presentation.

## Features

- **Fetch Fundamental Data**: Download and save company fundamental data using EODHD's API.
- **Exchange Symbol Management**: Retrieve and manage symbols for different exchanges.
- **Generate HTML Reports**: Convert downloaded data into readable and interactive HTML reports.
- **Automate Workflows**: Scripts are designed for seamless integration into larger automation pipelines.
- **Advanced Tools**: Includes additional utilities for ETF data processing, market cap analysis, and JSON inspection.

## Prerequisites

1. Python 3.8 or higher.
2. A valid EODHD API key.
3. Install required Python packages:

```bash
pip install -r requirements.txt
```

4. Add your EODHD API key to a `.env` file:

```
EODHD_API_KEY=your_api_key_here
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/JeremyWhittaker/eodhd-fundamental-data-tools.git
cd eodhd-fundamental-data-tools
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up the directory structure for data:

```bash
mkdir -p data/exchanges
mkdir -p data/fundamental_data
```

## Usage

### Fetch Symbols for Exchanges

```bash
python get_symbols_from_exchange.py
```

This script retrieves symbols for all exchanges and saves them as JSON files in the `data/exchanges` directory.

### List Unique Exchanges

```bash
python get_unique_exchanges.py --country US
```

Lists all unique exchanges for the specified country code.

### Fetch Fundamental Data

```bash
python get_fundamental_data.py --country US --exchange NYSE --days 7
```

This command fetches fundamental data for symbols from the NYSE and saves them in `data/fundamental_data`.

### Generate HTML Reports

```bash
python generate_html.py --rss data/fundamental_data/aapl.us.json
```

Converts the JSON data of a specific company (e.g., `aapl.us.json`) into an interactive HTML report.

### Process ETF Data

```bash
python tools/etf_data_to_csv.py --json-dir data/fundamental_data --output-csv data/etfs.csv
```

Parses ETF JSON files to create a CSV file containing ETF data and peer relationships.

### Categorize Market Capitalizations

```bash
python tools/generate_market_cap_categories.py --data_dir data/fundamental_data --output_dir data/market_cap_categories
```

Categorizes stocks into market cap groups (e.g., nano, micro, small) and saves the results to CSV files.

### Inspect JSON Files

```bash
python tools/analyze_json.py --json-path data/fundamental_data/aapl.us.json
```

Logs the structure and key details of a JSON file for debugging and analysis.

## File Overview

- **`get_symbols_from_exchange.py`**: Retrieves and saves exchange symbols.
- **`get_unique_exchanges.py`**: Lists unique exchanges for a specified country.
- **`get_fundamental_data.py`**: Downloads fundamental data for symbols.
- **`generate_html.py`**: Generates HTML reports from fundamental data.

### Tools Subfolder

The `tools/` directory contains additional utilities for advanced data processing:

- **`etf_data_to_csv.py`**: Parses ETF data and creates CSV files, including peer overlap analysis.
- **`generate_market_cap_categories.py`**: Categorizes stocks into market cap groups and saves results to CSV.
- **`analyze_json.py`**: Inspects and logs the structure of JSON files for debugging.
- **`get_market_cap.py`**: Extracts market caps from JSON data and saves to CSV.
- **`get_market_caps.py`**: Processes market caps across multiple files.

## Contribution

Contributions are welcome! Please submit a pull request or raise an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to [EODHD](https://eodhd.com) for providing the API for financial data.
