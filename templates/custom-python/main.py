"""
Keboola Custom Python Script Template

This template demonstrates how to:
1. Read data from Keboola Storage input tables
2. Process the data using Python
3. Write results back to Keboola Storage output tables

For more information on Custom Python in Keboola, see:
https://help.keboola.com/transformations/python/
"""

import csv
import os
from pathlib import Path


def read_input_table(table_name: str) -> list[dict]:
    """
    Read a table from Keboola input mapping.

    Input tables are available in /data/in/tables/ directory.
    They are CSV files with headers.

    Args:
        table_name: Name of the input table (without .csv extension)

    Returns:
        List of dictionaries, where each dict represents a row

    Example:
        data = read_input_table('customers')
        # Returns: [{'id': '1', 'name': 'John'}, {'id': '2', 'name': 'Jane'}]
    """
    input_path = Path('/data/in/tables') / f'{table_name}.csv'

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input table '{table_name}' not found at {input_path}\n"
            f"Available files: {list(Path('/data/in/tables').glob('*.csv'))}"
        )

    with open(input_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_output_table(table_name: str, data: list[dict], columns: list[str] = None):
    """
    Write data to Keboola output mapping.

    Output tables are written to /data/out/tables/ directory.
    They must be CSV files with headers.

    Args:
        table_name: Name of the output table (without .csv extension)
        data: List of dictionaries to write
        columns: Optional list of column names. If None, uses keys from first row.

    Example:
        write_output_table('results', [
            {'customer_id': '1', 'total': '100'},
            {'customer_id': '2', 'total': '200'}
        ])
    """
    output_path = Path('/data/out/tables') / f'{table_name}.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        raise ValueError(f"Cannot write empty data to table '{table_name}'")

    if columns is None:
        columns = list(data[0].keys())

    with open(output_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Written {len(data)} rows to {table_name}.csv")


def read_config() -> dict:
    """
    Read configuration from Keboola.

    Configuration is available in /data/config.json file.
    This includes parameters set in the Keboola UI.

    Returns:
        Dictionary with configuration

    Example config.json:
        {
            "parameters": {
                "threshold": 100,
                "debug": false
            }
        }
    """
    import json

    config_path = Path('/data/config.json')

    if not config_path.exists():
        print("⚠ No config.json found, using empty configuration")
        return {}

    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def process_data(input_data: list[dict], threshold: int = 100) -> list[dict]:
    """
    Example data processing function.

    This function demonstrates a simple transformation:
    - Filters rows based on a threshold
    - Adds a new calculated column
    - Transforms existing columns

    Replace this with your actual business logic.

    Args:
        input_data: List of input records
        threshold: Minimum value threshold

    Returns:
        List of processed records
    """
    results = []

    for row in input_data:
        # Example: Convert amount to float and filter
        try:
            amount = float(row.get('amount', 0))
        except (ValueError, TypeError):
            print(f"⚠ Skipping row with invalid amount: {row}")
            continue

        # Apply business logic
        if amount >= threshold:
            results.append({
                'id': row.get('id'),
                'name': row.get('name'),
                'original_amount': amount,
                'amount_doubled': amount * 2,
                'category': 'high' if amount >= threshold * 2 else 'medium',
                'processed': True
            })

    return results


def main():
    """
    Main execution function.

    This is the entry point for your Custom Python script.
    It orchestrates reading inputs, processing data, and writing outputs.
    """
    print("Starting Keboola Custom Python Script...")

    # Step 1: Read configuration
    config = read_config()
    parameters = config.get('parameters', {})

    # Get threshold from config, with default fallback
    threshold = parameters.get('threshold', 100)
    debug = parameters.get('debug', False)

    if debug:
        print(f"Debug mode enabled")
        print(f"Configuration: {parameters}")

    # Step 2: Read input data
    # Replace 'input_table' with your actual input table name
    # or use the name from your input mapping
    print("\nReading input data...")
    input_data = read_input_table('input_table')
    print(f"✓ Read {len(input_data)} rows from input")

    if debug and input_data:
        print(f"Sample row: {input_data[0]}")

    # Step 3: Process the data
    print("\nProcessing data...")
    processed_data = process_data(input_data, threshold=threshold)
    print(f"✓ Processed {len(processed_data)} rows")

    # Step 4: Write output data
    print("\nWriting output data...")
    write_output_table('output_table', processed_data)

    # Step 5: Optional - Write summary statistics
    summary = [{
        'total_input_rows': len(input_data),
        'total_output_rows': len(processed_data),
        'threshold_used': threshold,
        'filter_rate': f"{len(processed_data) / len(input_data) * 100:.1f}%"
    }]
    write_output_table('summary', summary)

    print("\n✓ Script completed successfully!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        # Exit with error code so Keboola knows the script failed
        exit(1)
