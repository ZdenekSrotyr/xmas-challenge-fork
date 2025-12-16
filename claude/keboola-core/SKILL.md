# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/`
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-16T09:47:57.473968

---

## Overview

This skill provides comprehensive knowledge about the Keboola platform,
including API usage, best practices, and common pitfalls.

**When to activate this skill:**
- User asks about Keboola Storage API
- User needs help with Keboola Jobs API
- User asks about regional stacks or Stack URLs
- User encounters Keboola-related errors
- User wants to create Custom Python components/transformations
- User asks about component deployment or Docker
- User needs help with keboola.component library

---

<!-- Source: 01-core-concepts.md -->

# Core Concepts

## Overview

Keboola is a cloud-based data platform that enables you to extract, transform, and load data from various sources.

## Key Concepts

### Project
A project is the top-level container in Keboola. All your configurations, data, and orchestrations belong to a project.

### Storage
Keboola Storage is where your data lives. It consists of:
- **Buckets**: Logical containers for tables
- **Tables**: The actual data
- **Files**: Temporary file storage

### Components
Components are the building blocks:
- **Extractors**: Pull data from external sources
- **Transformations**: Process and modify data
- **Writers**: Send data to external destinations

## Authentication

Use Storage API tokens for authentication:

```python
import os
import requests

STORAGE_TOKEN = os.environ["KEBOOLA_TOKEN"]
STACK_URL = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")

headers = {
    "X-StorageApi-Token": STORAGE_TOKEN,
    "Content-Type": "application/json"
}

response = requests.get(
    f"https://{STACK_URL}/v2/storage/tables",
    headers=headers
)
```

## Regional Stacks

Keboola operates multiple regional stacks:
- **US**: connection.keboola.com
- **EU**: connection.eu-central-1.keboola.com
- **Azure**: connection.north-europe.azure.keboola.com

Always use your project's stack URL, not a hardcoded one.


---

<!-- Source: 02-storage-api.md -->

# Storage API

## Reading Tables

### List All Tables

```python
import requests
import os

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": token}
)

tables = response.json()
for table in tables:
    print(f"{table['id']}: {table['rowsCount']} rows")
```

### Export Table Data

```python
# Get table export URL
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

job_id = response.json()["id"]

# Poll for completion
import time
while True:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )

    job = job_response.json()
    if job["status"] in ["success", "error"]:
        break

    time.sleep(2)

# Download data
if job["status"] == "success":
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url)

    import csv
    import io

    reader = csv.DictReader(io.StringIO(data_response.text))
    data = list(reader)
```

## Writing Tables

### Create Table from CSV

```python
# Upload CSV file
csv_data = "id,name,value\n1,foo,100\n2,bar,200"

response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "name": "my_table",
        "dataString": csv_data
    }
)

job_id = response.json()["id"]
# Poll job until completion (same as above)
```

## Common Patterns

### Pagination

Large tables should be exported in chunks:

```python
def export_table_paginated(table_id, chunk_size=10000):
    """Export table in chunks."""
    offset = 0
    all_data = []

    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tables/{table_id}/data-preview",
            headers={"X-StorageApi-Token": token},
            params={
                "limit": chunk_size,
                "offset": offset
            }
        )

        chunk = response.json()
        if not chunk:
            break

        all_data.extend(chunk)
        offset += chunk_size

    return all_data
```

### Incremental Loads

Use changed_since parameter for incremental updates:

```python
from datetime import datetime, timedelta

# Get data changed in last 24 hours
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token},
    params={"changedSince": yesterday}
)
```


---

<!-- Source: 03-common-pitfalls.md -->

# Common Pitfalls

## 1. Hardcoding Stack URLs

**Problem**: Using `connection.keboola.com` for all projects

**Solution**: Always use environment variables:

```python
# ❌ WRONG
stack_url = "connection.keboola.com"

# ✅ CORRECT
stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
```

## 2. Not Handling Job Polling

**Problem**: Assuming async operations complete immediately

**Solution**: Always poll until job finishes:

```python
def wait_for_job(job_id, timeout=300):
    """Wait for job completion with timeout."""
    start = time.time()

    while time.time() - start < timeout:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )

        job = response.json()

        if job["status"] == "success":
            return job
        elif job["status"] == "error":
            raise Exception(f"Job failed: {job.get('error', {}).get('message')}")

        time.sleep(2)

    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")
```

## 3. Ignoring Rate Limits

**Problem**: Making too many API calls too quickly

**Solution**: Implement exponential backoff:

```python
import time
from requests.exceptions import HTTPError

def api_call_with_retry(url, headers, max_retries=3):
    """Make API call with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

    raise Exception("Max retries exceeded")
```

## 4. Not Validating Table IDs

**Problem**: Using invalid table ID format

**Solution**: Validate format before API calls:

```python
import re

def validate_table_id(table_id):
    """Validate Keboola table ID format."""
    pattern = r'^(in|out)\.c-[a-z0-9-]+\.[a-z0-9_-]+$'

    if not re.match(pattern, table_id):
        raise ValueError(
            f"Invalid table ID: {table_id}. "
            f"Expected format: stage.c-bucket.table"
        )

    return True

# Usage
validate_table_id("in.c-main.customers")  # ✓
validate_table_id("my_table")  # ✗ Raises ValueError
```

## 5. Missing Error Handling

**Problem**: Not handling API errors gracefully

**Solution**: Always check response status:

```python
def safe_api_call(url, headers):
    """Make API call with proper error handling."""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        print("Request timed out")
        return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Invalid token")
        elif e.response.status_code == 404:
            print("Resource not found")
        else:
            print(f"HTTP error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```


---

---

<!-- Source: 04-custom-python-components.md -->

# Custom Python Components

## Overview

For complex transformations and custom logic, you can build Custom Python Components using the `keboola.component` library. These components run as Docker containers in Keboola and can read from Storage, process data, and write back results.

**When to use Custom Python Components:**
- Complex data transformations requiring custom Python libraries
- Need for state management (incremental loads)
- Integration with external APIs requiring custom logic
- Reusable transformation logic across multiple projects

**For comprehensive component development, see:** `claude/component-developer/`

## Component Structure

### Basic Directory Structure

```
my-component/
├── src/
│   └── component.py          # Main component logic
├── tests/
│   └── test_component.py
├── data/                      # Local testing data
│   ├── in/
│   │   └── tables/
│   │       └── source.csv
│   ├── out/
│   │   └── tables/
│   └── config.json
├── Dockerfile
├── requirements.txt
└── component_config/
    └── component.json         # Configuration schema
```

### Component Code Example

```python
import csv
from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

class Component(ComponentBase):
    def __init__(self):
        super().__init__()

    def run(self):
        # Get parameters from config
        params = self.configuration.parameters
        multiplier = params.get('multiplier', 1)

        # Get input table
        input_tables = self.get_input_tables_definitions()
        if not input_tables:
            raise UserException("No input tables found")

        input_table = input_tables[0]

        # Process data
        output_data = []
        with open(input_table.full_path, 'r') as input_file:
            reader = csv.DictReader(input_file)
            for row in reader:
                # Transform data
                row['value'] = int(row['value']) * multiplier
                output_data.append(row)

        # Write output
        output_table_path = self.create_out_table_definition(
            'result.csv',
            incremental=False,
            primary_key=['id']
        )

        with open(output_table_path.full_path, 'w', newline='') as output_file:
            if output_data:
                writer = csv.DictWriter(output_file, fieldnames=output_data[0].keys())
                writer.writeheader()
                writer.writerows(output_data)

if __name__ == "__main__":
    try:
        comp = Component()
        comp.run()
    except UserException as exc:
        comp.logger.error(exc)
        exit(1)
    except Exception as exc:
        comp.logger.exception(exc)
        exit(2)
```

## Input/Output Mapping

### Configuration Format

```json
{
  "parameters": {
    "multiplier": 2
  },
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-main.source-table",
          "destination": "source.csv"
        }
      ]
    },
    "output": {
      "tables": [
        {
          "source": "result.csv",
          "destination": "out.c-main.result-table",
          "incremental": false,
          "primary_key": ["id"]
        }
      ]
    }
  }
}
```

### Accessing Input Tables

```python
# Get all input tables
input_tables = self.get_input_tables_definitions()

# Access specific table
for table in input_tables:
    print(f"Table: {table.name}")
    print(f"Path: {table.full_path}")
    print(f"Columns: {table.columns}")
```

### Creating Output Tables

```python
# Create output table with manifest
output_table = self.create_out_table_definition(
    'output.csv',
    incremental=False,
    primary_key=['id'],
    columns=['id', 'name', 'value']
)

# Write data
with open(output_table.full_path, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'name', 'value'])
    writer.writerow([1, 'foo', 100])
```

## Manifest Files

Manifest files describe table metadata. They are automatically created when using `create_out_table_definition()`:

```json
{
  "destination": "out.c-main.result",
  "incremental": false,
  "primary_key": ["id"],
  "columns": ["id", "name", "value"],
  "delimiter": ",",
  "enclosure": "\""
}
```

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ /code/src/

# Run component
CMD ["python", "-u", "/code/src/component.py"]
```

## Local Testing

### Setup Test Data

```bash
# Create directory structure
mkdir -p data/in/tables data/out/tables

# Add test CSV
echo "id,name,value" > data/in/tables/source.csv
echo "1,foo,100" >> data/in/tables/source.csv
echo "2,bar,200" >> data/in/tables/source.csv

# Create config
cat > data/config.json << EOF
{
  "parameters": {
    "multiplier": 2
  }
}
EOF
```

### Run Locally

```bash
# Set environment variables
export KBC_DATADIR="./data"

# Run component
python src/component.py

# Check output
cat data/out/tables/result.csv
```

### Run with Docker

```bash
# Build image
docker build -t my-component .

# Run container
docker run --rm \
  -v $(pwd)/data:/data \
  -e KBC_DATADIR=/data \
  my-component
```

## State Management

For incremental loads, use state files:

```python
from datetime import datetime

class Component(ComponentBase):
    def run(self):
        # Load previous state
        state = self.get_state_file()
        last_run = state.get('last_run', '2000-01-01')

        # Process only new data
        # ... processing logic ...

        # Save new state
        self.write_state_file({
            'last_run': datetime.now().isoformat()
        })
```

## Deployment

### Using Developer Portal

1. Register component via API:

```python
import requests

response = requests.post(
    f"https://{stack_url}/v2/storage/dev-branches/default/components",
    headers={"X-StorageApi-Token": token},
    json={
        "id": "my-org.my-component",
        "type": "transformation",
        "name": "My Component",
        "repository": {
            "type": "github",
            "url": "https://github.com/my-org/my-component",
            "tag": "1.0.0"
        }
    }
)
```

2. Push to GitHub with proper tags
3. Keboola builds Docker image automatically
4. Component becomes available in your project

### GitHub Repository Setup

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    tags:
      - '*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push
        run: |
          docker build -t my-component:${GITHUB_REF#refs/tags/} .
          # Keboola pulls from your repository
```

## Common Component Patterns

### Error Handling

```python
from keboola.component.exceptions import UserException

try:
    result = process_data(input_data)
except ValueError as e:
    # User-facing error (shown in Keboola UI)
    raise UserException(f"Invalid data format: {e}")
except Exception as e:
    # System error (triggers alert)
    raise
```

### Logging

```python
class Component(ComponentBase):
    def run(self):
        self.logging.info("Starting processing")
        self.logging.debug(f"Config: {self.configuration.parameters}")
        self.logging.warning("Found duplicate records")
        self.logging.error("Failed to process row")
```

### Configuration Schema

Define schema in `component_config/component.json`:

```json
{
  "type": "object",
  "required": ["multiplier"],
  "properties": {
    "multiplier": {
      "type": "integer",
      "title": "Multiplier",
      "description": "Value to multiply by",
      "minimum": 1
    }
  }
}
```

## Related Documentation

For comprehensive component development:
- **Component Architecture**: `claude/component-developer/guides/component-builder/architecture.md`
- **Testing Guide**: `claude/component-developer/guides/component-builder/running-and-testing.md`
- **Developer Portal**: `claude/component-developer/guides/component-builder/developer-portal.md`
- **Cookiecutter Template**: https://github.com/keboola/cookiecutter-python-component


---

## Metadata

```json
{
  "generated_at": "2025-12-16T09:47:57.473968",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0"
}
```

---

**End of Skill**