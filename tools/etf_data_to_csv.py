#!/usr/bin/env python3

import os
import csv
import json
import sys
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from math import isclose

try:
    from tqdm import tqdm
except ImportError:
    class tqdm:
        def __init__(self, iterable=None, total=None, desc="", **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
        def __iter__(self):
            return iter(self.iterable or [])
        def update(self, n=1):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Script to parse ETF JSON, create CSV, and filter peers by overlap."
    )
    parser.add_argument(
        "--peers",
        type=float,
        default=80.0,  # Default threshold is 80%
        help="Minimum overlap required to keep a peer, e.g., 80.0 => only store peers >= 80.0 overlap. Default: 80.0",
    )
    parser.add_argument(
        "--json-dir",
        type=str,
        default="../data/fundamental_data",
        help="Directory containing ETF JSON files."
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="../data/etfs.csv",
        help="Path to the output CSV."
    )
    return parser.parse_args()


def calculate_country_distribution(holdings):
    if not holdings:
        return ""
    country_counts = Counter(code.split(".")[-1] for code in holdings)
    total_holdings = sum(country_counts.values())
    country_percentages = {
        country: (count / total_holdings) * 100
        for country, count in country_counts.items()
    }
    sorted_countries = sorted(country_percentages.items(), key=lambda x: -x[1])
    return ",".join(f"{country}({round(value, 1)})" for country, value in sorted_countries)


def calculate_peers(etf_holdings_map):
    symbols = list(etf_holdings_map.keys())
    overlaps = defaultdict(dict)
    n = len(symbols)
    total_pairs = n * (n - 1) // 2

    with tqdm(total=total_pairs, desc="Calculating overlap among ETFs") as pbar:
        for i in range(len(symbols)):
            symA = symbols[i]
            setA = etf_holdings_map[symA]
            for j in range(i + 1, len(symbols)):
                symB = symbols[j]
                setB = etf_holdings_map[symB]
                union_size = len(setA.union(setB))
                if union_size == 0:
                    overlap_ab = 0.0
                else:
                    overlap_ab = (len(setA.intersection(setB)) / union_size) * 100
                overlaps[symA][symB] = overlap_ab
                overlaps[symB][symA] = overlap_ab
                pbar.update(1)

    result = {}
    for sym in symbols:
        sorted_peers = sorted(overlaps[sym].items(), key=lambda x: -x[1])
        result[sym] = sorted_peers
    return result


def main():
    args = parse_arguments()
    json_dir = args.json_dir
    output_csv = args.output_csv
    peers_threshold = args.peers

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    rows = []
    error_categories = defaultdict(list)

    etf_holdings_map = {}
    json_files = list(Path(json_dir).glob("*.json"))

    for json_file in tqdm(json_files, desc="Reading JSON files"):
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            general_data = data.get("General", {})
            if general_data.get("Type") == "ETF":
                symbol = general_data.get("Code", "")
                etf_data = data.get("ETF_Data", {})
                total_assets_raw = etf_data.get("TotalAssets", None)
                try:
                    total_assets = float(total_assets_raw)
                except (TypeError, ValueError):
                    error_categories["Invalid TotalAssets"].append(symbol)
                    rows.append([symbol, None, None, "", "", "", 0])
                    continue
                avg_mkt_cap = etf_data.get("Average_Mkt_Cap_Mil", "")
                holdings = etf_data.get("Holdings", {})
                holding_codes_plain = []
                holding_codes_display_list = []
                for code, info in holdings.items():
                    if "." in code and len(code.split(".")[-1]) == 2:
                        holding_codes_plain.append(code)
                        assets_percent = info.get("Assets_%", None)
                        if assets_percent is not None:
                            holding_codes_display_list.append(
                                f"{code}({assets_percent})"
                            )
                        else:
                            holding_codes_display_list.append(code)
                if not holding_codes_plain:
                    error_categories["No valid holdings"].append(symbol)
                    rows.append([symbol, total_assets, avg_mkt_cap, "", "", "", 0])
                    continue
                holding_codes_str = ",".join(holding_codes_display_list)
                country_dist_raw = calculate_country_distribution(holding_codes_plain)
                rows.append([
                    symbol,
                    total_assets,
                    avg_mkt_cap,
                    country_dist_raw,
                    holding_codes_str,
                    "",
                    0
                ])
                etf_holdings_map[symbol] = set(holding_codes_plain)
        except Exception as e:
            error_categories["Other Errors"].append(json_file.name)
            print(f"Error processing {json_file}: {e}")

    rows.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)

    peers_dict = calculate_peers(etf_holdings_map)

    for row in rows:
        symbol = row[0]
        if symbol in peers_dict and len(etf_holdings_map[symbol]) > 1:
            full_peers = peers_dict[symbol]
            filtered_peers = [(p_sym, val) for p_sym, val in full_peers
                              if val >= peers_threshold and len(etf_holdings_map[p_sym]) > 1]
            peer_str_list = [f"{p_sym}({round(val,1)})" for p_sym, val in filtered_peers]
            peers_str = ",".join(peer_str_list)
            row[5] = peers_str
            row[6] = len(filtered_peers)

    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Symbol",
            "Total Assets",
            "Average Mkt Cap (Mil)",
            "Country Holdings Distribution",
            "Holdings Codes",
            f"Peers >= {peers_threshold}",
            f"Num Peers >= {peers_threshold}"
        ])
        writer.writerows(rows)

    print(f"Processed {len(rows)} ETFs. Output saved to {output_csv}")
    if error_categories:
        print("\nSummary of Errors:")
        for category, symbols in error_categories.items():
            print(f"{category}: {', '.join(symbols)}")


if __name__ == "__main__":
    main()
