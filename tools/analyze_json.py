import os
import json
import argparse
import logging
import re

# Configure logging to display DEBUG messages with indentation
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()


def load_json(filepath):
    """
    Loads a JSON file and returns its content.
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            logger.debug(f"Successfully loaded JSON file: {filepath}\n")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error in file {filepath}: {e}")
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
    return None


def is_date_string(s):
    """
    Checks if a string matches common date formats (e.g., YYYY-MM-DD).
    """
    if not isinstance(s, str):
        return False
    # Simple regex for YYYY-MM-DD format
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', s))


def is_numeric_key_dict(d):
    """
    Checks if all keys in the dictionary are numeric strings.
    """
    if not isinstance(d, dict):
        return False
    return all(k.isdigit() for k in d.keys())


def detect_repetitive_keys(d, threshold):
    """
    Detects if a dictionary has a large number of keys with similar patterns.
    Returns True if repetitive, else False.
    """
    if not isinstance(d, dict):
        return False
    # Count keys that look like dates
    date_keys = [k for k in d.keys() if is_date_string(k)]
    numeric_keys = [k for k in d.keys() if k.isdigit()]
    if len(date_keys) >= threshold:
        return 'dates'
    elif len(numeric_keys) >= threshold:
        return 'numeric'
    return False


def inspect_json(data, depth=0, max_depth=3, list_sample_size=3, repetition_threshold=10, sample_size=5,
                 parent_keys=[]):
    """
    Recursively inspects the JSON data and logs detailed information.

    Parameters:
    - data: The JSON data to inspect.
    - depth: Current depth in the JSON structure.
    - max_depth: Maximum depth to traverse to prevent excessive output.
    - list_sample_size: Number of items to inspect within lists.
    - repetition_threshold: Number of similar keys to trigger summarization.
    - sample_size: Number of sample keys to display when summarizing.
    - parent_keys: List of parent keys leading to the current data.
    """
    indent = '    ' * depth
    if depth > max_depth:
        logger.debug(f"{indent}... (Max Depth Reached)")
        return

    if isinstance(data, dict):
        # Check for repetitive structures
        repetition_type = detect_repetitive_keys(data, repetition_threshold)
        if repetition_type:
            full_key = " -> ".join(parent_keys) if parent_keys else "Root"
            total = len(data)
            samples = list(data.keys())[:sample_size]
            if repetition_type == 'dates':
                logger.debug(
                    f"{indent}Repetitive Structure Detected: {total} date entries under '{parent_keys[-1] if parent_keys else 'Root'}'")
                logger.debug(f"{indent}Sample Keys: {samples}")
            elif repetition_type == 'numeric':
                logger.debug(
                    f"{indent}Repetitive Structure Detected: {total} numeric entries under '{parent_keys[-1] if parent_keys else 'Root'}'")
                logger.debug(f"{indent}Sample Keys: {samples}")
            logger.debug(f"{indent}... (Further keys not displayed)")
            return  # Skip further inspection of this repetitive structure

        for key, value in data.items():
            full_key = " -> ".join(parent_keys + [key])
            logger.debug(f"{indent}Key: '{key}' | Full Path: '{full_key}' | Type: {type(value).__name__}")
            # If the value is a dict or list, recurse
            if isinstance(value, (dict, list)):
                inspect_json(value, depth + 1, max_depth, list_sample_size, repetition_threshold, sample_size,
                             parent_keys + [key])
            else:
                # Log sample data for primitive types
                sample = repr(value)
                logger.debug(f"{indent}    Sample Data: {sample}")
        if not data:
            logger.debug(f"{indent}Empty dictionary.")
    elif isinstance(data, list):
        logger.debug(f"{indent}List | Length: {len(data)}")
        if data:
            # Inspect first few items in the list
            sample_size = min(list_sample_size, len(data))
            for i in range(sample_size):
                item = data[i]
                item_path = parent_keys + [f"[{i}]"]
                logger.debug(f"{indent}    Item {i + 1} | Type: {type(item).__name__}")
                if isinstance(item, (dict, list)):
                    inspect_json(item, depth + 2, max_depth, list_sample_size, repetition_threshold, sample_size,
                                 item_path)
                else:
                    sample = repr(item)
                    logger.debug(f"{indent}        Sample Data: {sample}")
            if len(data) > sample_size:
                remaining = len(data) - sample_size
                logger.debug(f"{indent}    ... {remaining} more items not displayed.")
        else:
            logger.debug(f"{indent}Empty list.")
    else:
        # For primitive types at the root
        logger.debug(f"{indent}Value: {repr(data)} | Type: {type(data).__name__}\n")


def main():
    """
    Main function to load and inspect the JSON file.
    """
    parser = argparse.ArgumentParser(description="Inspect and log the structure of a JSON file.")
    parser.add_argument(
        '--json-path',
        type=str,
        default='../data/fundamental_data/aapl.json',
        help='Path to the JSON file to inspect. Default is ../data/fundamental_data/aapl.us.json'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum depth to traverse the JSON structure. Default is 3'
    )
    parser.add_argument(
        '--list-sample-size',
        type=int,
        default=3,
        help='Number of items to sample within lists. Default is 3'
    )
    parser.add_argument(
        '--repetition-threshold',
        type=int,
        default=10,
        help='Number of similar keys to trigger summarization. Default is 10'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=5,
        help='Number of sample keys to display when summarizing. Default is 5'
    )
    args = parser.parse_args()

    # Load JSON data
    data = load_json(args.json_path)

    if data is not None:
        logger.debug("----- JSON Structure Overview -----\n")
        inspect_json(
            data,
            depth=0,
            max_depth=args.max_depth,
            list_sample_size=args.list_sample_size,
            repetition_threshold=args.repetition_threshold,
            sample_size=args.sample_size,
            parent_keys=[]
        )
        logger.debug("\n----- End of JSON Structure -----")
    else:
        logger.error("Failed to load JSON data. Exiting.")


if __name__ == "__main__":
    main()
