### README.md

```markdown
# Stock Market Data Fetcher

In order to create a quantitative investment strategy based on fundamental data, you need to have a robust local repository of data. This program downloads all stock, ETF, and mutual fund data from the [EODHD API](https://eodhistoricaldata.com/) and saves it as Parquet files for efficient storage and access. Additionally, the program generates HTML reports for analysis and provides examples demonstrating how to access various fields within the JSON files.

## Table of Contents
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Scripts Overview](#scripts-overview)
- [Usage](#usage)
  - [Get Exchange Symbols](#get-exchange-symbols)
  - [Fetch Fundamental Data](#fetch-fundamental-data)
  - [List Unique Exchanges](#list-unique-exchanges)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/stock-market-data-fetcher.git
    cd stock-market-data-fetcher
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Environment Setup

Create a `.env` file at the root directory and set the API key for EODHD:
```bash
EODHD_API_KEY=your_api_key_here
```

## Scripts Overview

1. `get_symbols_from_exchange.py`: Fetches exchange symbols from the EODHD API and saves them as JSON files for each exchange.
2. `get_fundamental_data.py`: Downloads and saves fundamental data for all assets (stocks, ETFs, mutual funds) as Parquet files for efficient storage and analysis.
3. `get_unique_exchanges.py`: Lists all unique exchanges available in the JSON files for a specific country.
4. **HTML Reports**: The scripts include functionality to generate HTML files summarizing saved data to make it easier to explore and analyze.

## Usage

### Get Exchange Symbols
To fetch symbols for all exchanges:
```bash
python get_symbols_from_exchange.py
```

### Fetch Fundamental Data
To download and save fundamental data for a specific country and exchange:
```bash
python get_fundamental_data.py --country US --exchange NASDAQ --output_dir ./data/fundamental_data --days 7
```

### List Unique Exchanges
To list all unique exchanges for a given country:
```bash
python get_unique_exchanges.py --country US
```

## Logging
- Logs are saved to `exchange_symbols.log`.
- You can monitor the log to check details about processed exchanges and error messages.

## Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch-name`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch-name`).
5. Create a pull request.

## License
This project is licensed under the MIT License. See `LICENSE` for more details.
```

### requirements.txt

```plaintext
requests
python-dotenv
tqdm
argparse
logging
json
datetime
pathlib
```

