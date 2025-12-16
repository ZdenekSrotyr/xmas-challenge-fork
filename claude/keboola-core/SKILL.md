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
- User wants to create custom Python transformations or components
- User asks about keboola.component library
- User needs help with Input/Output mapping
- User asks about component deployment or Docker configuration

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

<!-- Source: 04-custom-python-components.md -->

# Custom Python Components

## Overview

While you can interact with Keboola Storage directly via REST API, the recommended approach for custom Python transformations is to use the `keboola.component` library. This provides:
- Standardized component structure
- Automatic Input/Output mapping
- Configuration and manifest handling
- Error handling conventions
- Local testing capabilities

## Component Structure

A Keboola Python component follows this structure:

```
my-component/
├── src/
│   └── component.py          # Main component code
├── tests/
│   └── test_component.py     # Unit tests
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
├── component_config/
│   └── component.json        # Component definition
└── README.md
```

## Basic Component Template

### component.py

```python
import csv
from pathlib import Path
from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

class Component(ComponentBase):
    def __init__(self):
        super().__init__()

    def run(self):
        """
        Main execution method.
        Input tables are in: self.get_input_tables_definitions()
        Output tables go to: self.get_output_tables_definitions()
        """
        # Get parameters from configuration
        params = self.configuration.parameters
        
        # Read input table
        input_tables = self.get_input_tables_definitions()
        if not input_tables:
            raise UserException("No input tables specified")
        
        input_table = input_tables[0]
        input_path = Path(input_table.full_path)
        
        # Process data
        with open(input_path, 'r') as input_file:
            reader = csv.DictReader(input_file)
            data = list(reader)
            
            # Your transformation logic here
            processed_data = self.process_data(data, params)
        
        # Write output table
        output_tables = self.get_output_tables_definitions()
        if output_tables:
            output_table = output_tables[0]
            output_path = Path(output_table.full_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='') as output_file:
                if processed_data:
                    writer = csv.DictWriter(output_file, fieldnames=processed_data[0].keys())
                    writer.writeheader()
                    writer.writerows(processed_data)
    
    def process_data(self, data, params):
        """Your custom processing logic."""
        # Example: filter rows based on parameter
        threshold = params.get('threshold', 0)
        return [row for row in data if int(row.get('value', 0)) > threshold]

if __name__ == "__main__":
    try:
        comp = Component()
        comp.run()
    except UserException as exc:
        print(exc)
        exit(1)
    except Exception as exc:
        print(exc)
        exit(2)
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code/

# Install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /code/src/

# Run component
CMD ["python", "-u", "src/component.py"]
```

### requirements.txt

```
keboola.component==1.8.1
```

## Input/Output Mapping Configuration

### Configuration Format

When running your component in Keboola, you configure Input/Output mapping via the UI or API:

```json
{
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-main.customers",
          "destination": "customers.csv",
          "columns": ["id", "name", "value"]
        }
      ]
    },
    "output": {
      "tables": [
        {
          "source": "output.csv",
          "destination": "out.c-main.processed",
          "incremental": false,
          "primary_key": ["id"]
        }
      ]
    }
  },
  "parameters": {
    "threshold": 100
  }
}
```

### Accessing Input Tables

```python
# Get all input tables
input_tables = self.get_input_tables_definitions()

for table in input_tables:
    print(f"Table: {table.name}")
    print(f"Path: {table.full_path}")
    print(f"Columns: {table.columns}")
    
    # Read the CSV file
    with open(table.full_path, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
```

### Writing Output Tables

```python
# Get output table definition
output_tables = self.get_output_tables_definitions()
output_table = output_tables[0]

# Write data
with open(output_table.full_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'name', 'processed_value'])
    writer.writeheader()
    writer.writerows(processed_data)

# Create manifest for metadata (optional)
self.write_manifest(output_table.full_path, {
    'primary_key': ['id'],
    'incremental': False
})
```

## Local Testing

### Test Data Structure

Create a local data folder:

```
data/
├── in/
│   └── tables/
│       └── customers.csv
├── out/
│   └── tables/
└── config.json
```

### config.json

```json
{
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-main.customers",
          "destination": "customers.csv"
        }
      ]
    },
    "output": {
      "tables": [
        {
          "source": "output.csv",
          "destination": "out.c-main.processed"
        }
      ]
    }
  },
  "parameters": {
    "threshold": 100
  }
}
```

### Running Locally

```bash
# Set environment variable
export KBC_DATADIR=./data/

# Run component
python src/component.py

# Or with Docker
docker build -t my-component .
docker run --rm -v $(pwd)/data:/data -e KBC_DATADIR=/data my-component
```

## State Management (Incremental Loads)

For incremental processing, use state files:

```python
from keboola.component.base import ComponentBase
import json
from datetime import datetime

class Component(ComponentBase):
    def run(self):
        # Load previous state
        state = self.get_state_file()
        last_run = state.get('last_run_timestamp')
        
        # Process only new data
        if last_run:
            print(f"Loading data since {last_run}")
            # Filter data based on last_run
        
        # Process data...
        
        # Save new state
        new_state = {
            'last_run_timestamp': datetime.now().isoformat(),
            'rows_processed': len(processed_data)
        }
        self.write_state_file(new_state)
```

## Error Handling

### User Errors vs System Errors

```python
from keboola.component.exceptions import UserException

# User configuration error (exit code 1)
if not params.get('required_param'):
    raise UserException("Missing required parameter: required_param")

# System error (exit code 2)
try:
    # Some operation
    process_data()
except Exception as e:
    # Log error and re-raise
    print(f"System error: {e}")
    raise
```

## Deployment

### Quick Start with Cookiecutter

Use the official template:

```bash
pip install cookiecutter
cookiecutter gh:keboola/cookiecutter-python-component
```

### GitHub Repository Setup

1. Push your component to GitHub
2. Set up GitHub Actions for CI/CD:

```yaml
# .github/workflows/build.yml
name: Build and Deploy

on:
  push:
    tags:
      - '*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push Docker image
        uses: docker/build-push-action@v2
        with:
          push: true
          tags: your-registry/my-component:${{ github.ref_name }}
```

### Register in Developer Portal

Register your component via API:

```python
import requests

response = requests.post(
    "https://connection.keboola.com/v2/storage/dev-branches/",
    headers={"X-StorageApi-Token": token},
    json={
        "name": "my-component",
        "type": "transformation",
        "repository": {
            "type": "github",
            "uri": "https://github.com/username/my-component"
        }
    }
)
```

## Best Practices

### 1. Always Use keboola.component Library

```python
# ❌ WRONG: Direct API calls in component
import requests
response = requests.get(f"https://{stack_url}/v2/storage/tables/{table_id}")

# ✅ CORRECT: Use component framework
from keboola.component.base import ComponentBase
input_tables = self.get_input_tables_definitions()
```

### 2. Validate Input Early

```python
def run(self):
    params = self.configuration.parameters
    
    # Validate required parameters
    required = ['threshold', 'column_name']
    missing = [p for p in required if p not in params]
    if missing:
        raise UserException(f"Missing required parameters: {', '.join(missing)}")
    
    # Continue with processing...
```

### 3. Log Progress

```python
import logging

logging.info(f"Processing {len(data)} rows")
logging.debug(f"Parameters: {params}")
logging.warning(f"Skipped {skipped} invalid rows")
```

### 4. Handle Large Files Efficiently

```python
# ❌ WRONG: Loading entire file into memory
with open(input_path) as f:
    data = list(csv.DictReader(f))

# ✅ CORRECT: Process in chunks
def process_chunks(input_path, output_path, chunk_size=10000):
    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        chunk = []
        for row in reader:
            chunk.append(process_row(row))
            if len(chunk) >= chunk_size:
                writer.writerows(chunk)
                chunk = []
        
        if chunk:
            writer.writerows(chunk)
```

## Related Documentation

For component development details, refer to the component-developer documentation:
- Architecture patterns
- Testing strategies
- CI/CD setup
- Developer Portal integration


---

## Metadata

```json
{
  "generated_at": "2025-12-16T09:47:57.473968",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0",
  "coverage": {
    "storage_api": "complete",
    "jobs_api": "complete",
    "custom_components": "complete",
    "component_deployment": "complete"
  }
}
```

---

**End of Skill**