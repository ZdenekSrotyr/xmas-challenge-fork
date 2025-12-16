# Component Development

## Overview

Keboola components are Docker containers that follow the Common Interface specification for processing data. They communicate with Keboola exclusively through the filesystem at `/data`.

## Component Types

- **Extractors**: Pull data from external sources
- **Writers**: Send data to external destinations
- **Applications**: Process or transform data

Note: Don't include component type names ('extractor', 'writer', 'application') in the component name itself.

## Project Structure

```
my-component/
├── src/
│   ├── component.py          # Main logic with run() function
│   └── configuration.py      # Configuration validation
├── component_config/
│   ├── component_config.json           # Configuration schema
│   ├── component_long_description.md   # Detailed docs
│   └── component_short_description.md  # Brief description
├── tests/
│   └── test_component.py     # Unit tests
├── data/                     # Local data folder (gitignored)
│   ├── config.json           # Example config for local testing
│   ├── in/                   # Input tables and files
│   └── out/                  # Output tables and files
├── .github/workflows/
│   └── push.yml              # CI/CD deployment
├── Dockerfile                # Container definition
└── pyproject.toml            # Python dependencies
```

## Data Folder Contract

Components communicate with Keboola through the `/data` directory:

**INPUT** (read-only):
- `config.json` - Component configuration from UI
- `in/tables/*.csv` - Input tables with `.manifest` files
- `in/files/*` - Input files
- `in/state.json` - Previous run state (for incremental processing)

**OUTPUT** (write):
- `out/tables/*.csv` - Output tables with `.manifest` files
- `out/files/*` - Output files
- `out/state.json` - New state for next run

**IMPORTANT**: The Keboola platform automatically creates all data directories (`data/in/`, `data/out/tables/`, `data/out/files/`, etc.). You **never** need to call `mkdir()` or create these directories manually in your component code.

## Basic Component Implementation

```python
from keboola.component import CommonInterface
import logging
import sys
import traceback

REQUIRED_PARAMETERS = ['api_key', 'endpoint']

class Component(CommonInterface):
    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # 1. Validate configuration
            self.validate_configuration(REQUIRED_PARAMETERS)
            params = self.configuration.parameters

            # 2. Load state for incremental processing
            state = self.get_state_file()
            last_timestamp = state.get('last_timestamp')

            # 3. Process input tables
            input_tables = self.get_input_tables_definitions()
            for table in input_tables:
                self._process_table(table)

            # 4. Create output tables with manifests
            self._create_output_tables()

            # 5. Save state for next run
            self.write_state_file({
                'last_timestamp': current_timestamp
            })

        except ValueError as err:
            # User errors (configuration/input issues)
            logging.error(str(err))
            print(err, file=sys.stderr)
            sys.exit(1)
        except Exception as err:
            # System errors (unhandled exceptions)
            logging.exception("Unhandled error occurred")
            traceback.print_exc(file=sys.stderr)
            sys.exit(2)

if __name__ == '__main__':
    try:
        comp = Component()
        comp.run()
    except Exception as e:
        logging.exception("Component execution failed")
        sys.exit(2)
```

## Configuration Schema

Define configuration parameters in `component_config/component_config.json`:

```json
{
  "type": "object",
  "title": "Configuration",
  "required": ["api_key", "endpoint"],
  "properties": {
    "#api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your API authentication token",
      "format": "password"
    },
    "endpoint": {
      "type": "string",
      "title": "API Endpoint",
      "description": "Base URL for the API"
    },
    "incremental": {
      "type": "boolean",
      "title": "Incremental Load",
      "description": "Only fetch data since last run",
      "default": false
    }
  }
}
```

### Sensitive Data Handling

Prefix parameter names with `#` to enable automatic hashing:
```json
{
  "#password": {
    "type": "string",
    "title": "Password",
    "format": "password"
  }
}
```

### UI Elements

**Code Editor** (ACE editor for multi-line input):
```json
{
  "query": {
    "type": "string",
    "title": "SQL Query",
    "format": "textarea",
    "options": {
      "ace": {
        "mode": "sql"
      }
    }
  }
}
```

**Test Connection Button**:
```json
{
  "test_connection": {
    "type": "button",
    "title": "Test Connection",
    "options": {
      "syncAction": "test-connection"
    }
  }
}
```

## CSV Processing

Always process CSV files efficiently using generators:

```python
import csv

def process_input_table(table_def):
    with open(table_def.full_path, 'r', encoding='utf-8') as in_file:
        # Handle null characters with generator
        lazy_lines = (line.replace('\0', '') for line in in_file)
        reader = csv.DictReader(lazy_lines, dialect='kbc')

        for row in reader:
            # Process row by row for memory efficiency
            yield process_row(row)
```

## Creating Output Tables

Create output tables with proper schema definitions:

```python
from collections import OrderedDict
from keboola.component.dao import ColumnDefinition, BaseType

# Define schema
schema = OrderedDict({
    "id": ColumnDefinition(
        data_types=BaseType.integer(),
        primary_key=True
    ),
    "name": ColumnDefinition(),
    "value": ColumnDefinition(
        data_types=BaseType.numeric(length="10,2")
    )
})

# Create table definition
out_table = self.create_out_table_definition(
    name="results.csv",
    destination="out.c-data.results",
    schema=schema,
    incremental=True
)

# Write data
import csv
with open(out_table.full_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=out_table.column_names)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

# Write manifest
self.write_manifest(out_table)
```

## State Management for Incremental Processing

Implement proper state handling for incremental loads:

```python
def run_incremental(self):
    # Load previous state
    state = self.get_state_file()
    last_timestamp = state.get('last_timestamp', '1970-01-01T00:00:00Z')

    # Fetch only new data since last_timestamp
    new_data = self._fetch_data_since(last_timestamp)

    # Process and save data
    self._process_data(new_data)

    # Update state with current timestamp
    from datetime import datetime, timezone
    current_timestamp = datetime.now(timezone.utc).isoformat()
    self.write_state_file({
        'last_timestamp': current_timestamp,
        'records_processed': len(new_data)
    })
```

## Error Handling

Follow Keboola's error handling conventions:

- **Exit code 1**: User errors (configuration problems, invalid inputs)
- **Exit code 2**: System errors (unhandled exceptions, application errors)

```python
try:
    # Component logic
    validate_inputs(params)
    result = perform_operation()

except ValueError as err:
    # User-fixable errors
    logging.error(f"Configuration error: {err}")
    print(err, file=sys.stderr)
    sys.exit(1)

except requests.HTTPError as err:
    # API errors
    logging.error(f"API request failed: {err}")
    print(f"Failed to connect to API: {err.response.status_code}", file=sys.stderr)
    sys.exit(1)

except Exception as err:
    # Unhandled exceptions
    logging.exception("Unhandled error in component execution")
    traceback.print_exc(file=sys.stderr)
    sys.exit(2)
```

## Local Development

### Running Locally

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Set data directory environment variable
export KBC_DATADIR=./data

# Run component
python src/component.py
```

### Using Docker

```bash
# Build image
docker build -t my-component:latest .

# Run with mounted data folder
docker run --rm \
  -v $(pwd)/data:/data \
  -e KBC_DATADIR=/data \
  my-component:latest
```

### Prepare Test Data

Create `data/config.json` with example parameters:

```json
{
  "parameters": {
    "api_key": "your_key_here",
    "#password": "test_password",
    "from_date": "2024-01-01",
    "incremental": false
  }
}
```

Create sample input tables:

```bash
mkdir -p data/in/tables
cat > data/in/tables/input.csv <<EOF
id,name,email
1,John Doe,john@example.com
2,Jane Smith,jane@example.com
EOF
```

## Best Practices

### DO:

- Use `CommonInterface` class for all Keboola interactions
- Validate configuration early with `validate_configuration()`
- Process CSV files with generators for memory efficiency
- Always specify `encoding='utf-8'` for file operations
- Use proper exit codes (1 for user errors, 2 for system errors)
- Define explicit schemas for output tables
- Implement state management for incremental processing
- Write comprehensive tests
- Quote all SQL identifiers (`"column_name"`, not `column_name`)

### DON'T:

- Load entire CSV files into memory
- Hard-code configuration values
- Skip configuration validation
- Forget to write manifests for output tables
- Skip state file management for incremental loads
- Forget to handle null characters in CSV files
- Call `mkdir()` for platform-managed directories (in/, out/, tables/, files/)

## Dockerfile

```dockerfile
FROM python:3.11-alpine

# Install dependencies
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ /code/src/

# Set entrypoint with unbuffered output
ENTRYPOINT ["python", "-u", "/code/src/component.py"]
```

## CI/CD Deployment

### GitHub Actions Workflow

```yaml
# .github/workflows/push.yml
name: Build and Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t my-component:${{ github.ref_name }} .

      - name: Run tests
        run: docker-compose run --rm test

      - name: Deploy to Keboola
        env:
          KBC_DEVELOPERPORTAL_USERNAME: ${{ secrets.KBC_USERNAME }}
          KBC_DEVELOPERPORTAL_PASSWORD: ${{ secrets.KBC_PASSWORD }}
        run: ./deploy.sh
```

### Version Management

Follow semantic versioning:

- **v1.0.0** - Major release (breaking changes)
- **v1.1.0** - Minor release (new features)
- **v1.0.1** - Patch release (bug fixes)

```bash
# Tag and push
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Testing

### Unit Tests

```python
import unittest
from src.component import Component

class TestComponent(unittest.TestCase):
    def test_configuration_validation(self):
        """Test that required parameters are validated."""
        # Test implementation

    def test_csv_processing(self):
        """Test CSV reading and writing with proper encoding."""
        # Test implementation

    def test_state_management(self):
        """Test state file persistence."""
        # Test implementation
```

Run tests:

```bash
# Using unittest
python -m unittest discover -s tests

# Using pytest
pytest tests/ -v --cov=src
```

## Code Quality

Use Ruff for code formatting and linting:

```bash
# Format code
ruff format .

# Lint and auto-fix issues
ruff check --fix .
```

## Resources

- [Keboola Developer Docs](https://developers.keboola.com/)
- [Python Component Library](https://github.com/keboola/python-component)
- [Component Tutorial](https://developers.keboola.com/extend/component/tutorial/)
- [Cookiecutter Template](https://github.com/keboola/cookiecutter-python-component)

## Rate Limiting in Components

Components must handle Storage API rate limits gracefully to avoid job failures.

### Implementing Rate Limit Handling

```python
import time
import logging
from requests.exceptions import HTTPError

class Component(CommonInterface):
    def _make_api_request(self, url, method='GET', **kwargs):
        """Make API request with rate limit handling."""
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, **kwargs)
                elif method == 'POST':
                    response = requests.post(url, **kwargs)
                
                # Log rate limit status
                remaining = response.headers.get('X-RateLimit-Remaining')
                if remaining and int(remaining) < 50:
                    logging.warning(f"Rate limit low: {remaining} requests remaining")
                
                response.raise_for_status()
                return response.json()
            
            except HTTPError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logging.warning(
                        f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {retry_after}s..."
                    )
                    time.sleep(retry_after)
                    continue
                else:
                    raise
        
        raise Exception("Rate limit retries exhausted")
    
    def run(self):
        try:
            # Use rate-limit-aware API calls
            tables = self._make_api_request(
                f"https://{self.configuration.stack_url}/v2/storage/tables",
                headers={"X-StorageApi-Token": self.configuration.token}
            )
            
            # Process tables...
        
        except Exception as err:
            logging.exception("Component execution failed")
            sys.exit(2)
```

### Batch Processing to Reduce API Calls

```python
def process_tables_efficiently(self):
    """Process multiple tables with minimal API calls."""
    # ❌ BAD - One API call per table
    for table_id in table_ids:
        table_detail = self._make_api_request(
            f"{stack_url}/v2/storage/tables/{table_id}"
        )
    
    # ✅ GOOD - Single API call for all tables
    all_tables = self._make_api_request(
        f"{stack_url}/v2/storage/tables"
    )
    tables_by_id = {t['id']: t for t in all_tables}
    
    for table_id in table_ids:
        table_detail = tables_by_id.get(table_id)
```

### Testing Rate Limit Handling

```python
import unittest
from unittest.mock import patch, Mock

class TestRateLimitHandling(unittest.TestCase):
    @patch('requests.get')
    def test_retry_on_rate_limit(self, mock_get):
        """Test that component retries on 429 responses."""
        # First call returns 429, second succeeds
        response_429 = Mock()
        response_429.status_code = 429
        response_429.headers = {'Retry-After': '1'}
        response_429.raise_for_status.side_effect = HTTPError(response=response_429)
        
        response_200 = Mock()
        response_200.status_code = 200
        response_200.json.return_value = {'data': 'success'}
        
        mock_get.side_effect = [response_429, response_200]
        
        component = Component()
        result = component._make_api_request('https://example.com')
        
        self.assertEqual(result['data'], 'success')
        self.assertEqual(mock_get.call_count, 2)
```
