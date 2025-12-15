# Keboola Custom Python Template

A ready-to-use template for creating Custom Python scripts in Keboola.

## What This Template Does

This template provides a working example that:

1. Reads data from Keboola Storage (input tables)
2. Processes the data with configurable parameters
3. Writes results back to Keboola Storage (output tables)
4. Includes error handling and logging
5. Demonstrates best practices for Keboola Custom Python

## Quick Start

### 1. Copy the Template

Copy the contents of this template to your Keboola Custom Python transformation:

```bash
# Copy main.py to your transformation
# Copy requirements.txt if you need additional packages
```

### 2. Configure Input Mapping

In Keboola UI, set up your input mapping:

- **Source**: Select your input table from Storage (e.g., `in.c-main.customers`)
- **File name**: `input_table.csv`

### 3. Configure Output Mapping

Set up your output mapping:

- **Source**: `output_table.csv`
- **Destination**: Your target table in Storage (e.g., `out.c-main.results`)
- **Optional**: Also map `summary.csv` for statistics

### 4. Add Parameters (Optional)

In the transformation configuration, add parameters:

```json
{
  "threshold": 100,
  "debug": false
}
```

### 5. Run the Transformation

Click "Run Transformation" in Keboola UI.

## File Structure

```
custom-python/
├── main.py              # Main script with data processing logic
├── requirements.txt     # Python package dependencies
└── README.md           # This file
```

## How It Works

### Reading Input Data

```python
# Input tables are in /data/in/tables/
input_data = read_input_table('input_table')
# Returns: [{'column1': 'value1', 'column2': 'value2'}, ...]
```

### Processing Data

```python
# Your business logic here
processed_data = process_data(input_data, threshold=100)
```

### Writing Output Data

```python
# Output tables go to /data/out/tables/
write_output_table('output_table', processed_data)
```

### Reading Configuration

```python
# Configuration from Keboola UI
config = read_config()
threshold = config.get('parameters', {}).get('threshold', 100)
```

## Customization

### Modify the Processing Logic

Edit the `process_data()` function in `main.py`:

```python
def process_data(input_data: list[dict], threshold: int = 100) -> list[dict]:
    """
    Replace this with your actual business logic.
    """
    results = []
    for row in input_data:
        # Your processing here
        results.append({
            'id': row['id'],
            'result': your_calculation(row)
        })
    return results
```

### Add Multiple Input Tables

```python
# Read from multiple sources
customers = read_input_table('customers')
orders = read_input_table('orders')

# Join or process together
results = process_multiple_tables(customers, orders)
```

### Add Python Packages

Edit `requirements.txt` and uncomment or add packages:

```txt
pandas==2.1.4
numpy==1.26.3
requests==2.31.0
```

## Common Patterns

### Pattern 1: Data Filtering

```python
def filter_high_value_customers(customers: list[dict]) -> list[dict]:
    return [
        customer for customer in customers
        if float(customer.get('lifetime_value', 0)) > 10000
    ]
```

### Pattern 2: Data Aggregation

```python
def aggregate_by_category(data: list[dict]) -> list[dict]:
    from collections import defaultdict

    totals = defaultdict(float)
    for row in data:
        category = row.get('category')
        amount = float(row.get('amount', 0))
        totals[category] += amount

    return [
        {'category': cat, 'total': total}
        for cat, total in totals.items()
    ]
```

### Pattern 3: Data Enrichment

```python
def enrich_with_external_data(data: list[dict]) -> list[dict]:
    """
    Add data from external API or calculation.
    """
    results = []
    for row in data:
        enriched = row.copy()
        enriched['enriched_field'] = calculate_something(row)
        results.append(enriched)
    return results
```

### Pattern 4: Error Handling

```python
def safe_process_row(row: dict) -> dict | None:
    """
    Process a single row with error handling.
    """
    try:
        return {
            'id': row['id'],
            'value': float(row['amount']) * 2
        }
    except (KeyError, ValueError) as e:
        print(f"⚠ Error processing row {row}: {e}")
        return None

# Use with filter(None, ...) to remove failed rows
results = list(filter(None, [safe_process_row(r) for r in input_data]))
```

## Debugging

### Enable Debug Mode

Add to your configuration:

```json
{
  "debug": true
}
```

This will print:
- Configuration parameters
- Sample rows
- Processing statistics

### Check Data Directories

```python
# List available input files
import os
print(os.listdir('/data/in/tables'))

# Check if specific file exists
from pathlib import Path
if Path('/data/in/tables/input_table.csv').exists():
    print("Input file found!")
```

### Print Sample Data

```python
# Print first few rows
for i, row in enumerate(input_data[:5]):
    print(f"Row {i}: {row}")
```

## Best Practices

1. **Use Type Hints**: Makes code more readable and catches errors early
   ```python
   def process_data(data: list[dict], threshold: int) -> list[dict]:
   ```

2. **Handle Missing Data**: Always check if fields exist
   ```python
   value = row.get('field', default_value)
   ```

3. **Validate Input**: Check data types and values
   ```python
   try:
       amount = float(row['amount'])
   except (ValueError, KeyError):
       print(f"Invalid row: {row}")
       continue
   ```

4. **Log Progress**: Use print statements for visibility
   ```python
   print(f"Processing {len(data)} rows...")
   print(f"✓ Completed in {elapsed}s")
   ```

5. **Keep Requirements Minimal**: Only install packages you need
   - Faster execution
   - Fewer dependency conflicts

6. **Exit with Error Codes**: Let Keboola know if something failed
   ```python
   if critical_error:
       print(f"✗ Critical error: {error}")
       exit(1)
   ```

## Troubleshooting

### FileNotFoundError: Input table not found

- Check your input mapping in Keboola UI
- Ensure the file name matches exactly (case-sensitive)
- Verify the source table exists and has data

### Empty output files

- Make sure your processing function returns data
- Check if your filters are too restrictive
- Enable debug mode to see what's happening

### Module not found

- Add the package to `requirements.txt`
- Make sure the version is compatible with Keboola's Python version
- Check package name spelling

### Script timeout

- Reduce data volume (use filtering in input mapping)
- Optimize your processing logic
- Consider using batch processing
- Remove unnecessary debug prints in production

## Examples

### Example 1: Customer Segmentation

```python
def segment_customers(customers: list[dict]) -> list[dict]:
    """
    Segment customers by purchase behavior.
    """
    segments = []
    for customer in customers:
        total_purchases = float(customer.get('total_purchases', 0))

        if total_purchases > 10000:
            segment = 'VIP'
        elif total_purchases > 1000:
            segment = 'Regular'
        else:
            segment = 'New'

        segments.append({
            'customer_id': customer['id'],
            'name': customer['name'],
            'segment': segment,
            'total_purchases': total_purchases
        })

    return segments
```

### Example 2: Sales Report

```python
def generate_sales_report(orders: list[dict]) -> list[dict]:
    """
    Generate daily sales summary.
    """
    from collections import defaultdict
    from datetime import datetime

    daily_sales = defaultdict(lambda: {'revenue': 0, 'order_count': 0})

    for order in orders:
        date = order.get('order_date', '')[:10]  # YYYY-MM-DD
        revenue = float(order.get('total', 0))

        daily_sales[date]['revenue'] += revenue
        daily_sales[date]['order_count'] += 1

    return [
        {
            'date': date,
            'revenue': stats['revenue'],
            'order_count': stats['order_count'],
            'avg_order_value': stats['revenue'] / stats['order_count']
        }
        for date, stats in sorted(daily_sales.items())
    ]
```

### Example 3: Data Quality Check

```python
def check_data_quality(data: list[dict]) -> list[dict]:
    """
    Validate data quality and flag issues.
    """
    quality_report = []

    for i, row in enumerate(data):
        issues = []

        # Check required fields
        if not row.get('id'):
            issues.append('missing_id')

        # Check data types
        try:
            float(row.get('amount', 0))
        except ValueError:
            issues.append('invalid_amount')

        # Check ranges
        if float(row.get('amount', 0)) < 0:
            issues.append('negative_amount')

        quality_report.append({
            'row_number': i + 1,
            'has_issues': len(issues) > 0,
            'issues': ', '.join(issues) if issues else 'OK',
            'original_data': str(row)
        })

    return quality_report
```

## Resources

- [Keboola Custom Python Documentation](https://help.keboola.com/transformations/python/)
- [Keboola Storage API](https://developers.keboola.com/integrate/storage/)
- [Python CSV Module](https://docs.python.org/3/library/csv.html)

## Support

If you encounter issues:

1. Check the transformation logs in Keboola UI
2. Enable debug mode for more details
3. Verify input/output mapping configuration
4. Test with a small data sample first

## License

This template is provided as-is for use with Keboola Platform.
