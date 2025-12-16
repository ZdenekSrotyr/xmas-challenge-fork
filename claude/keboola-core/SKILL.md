# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/` + Custom Python Components section
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-16T09:47:57.473968
> Updated: 2025-12-16 (Added Custom Python Components)

---

## Overview

This skill provides comprehensive knowledge about the Keboola platform,
including API usage, best practices, and common pitfalls.

**When to activate this skill:**
- User asks about Keboola Storage API
- User needs help with Keboola Jobs API
- User asks about regional stacks or Stack URLs
- User encounters Keboola-related errors
- User wants to create Custom Python components or transformations
- User asks about deploying Python code to Keboola
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

---

<!-- Source: 04-custom-python-components.md -->

# Custom Python Components

## Overview

For production deployments, use the **Custom Python Component** framework instead of direct API calls. This approach provides:
- Standardized input/output handling
- Automatic manifest file processing
- Built-in state management
- Docker containerization
- Integration with Keboola Developer Portal

## Component Structure

### Directory Layout

```
my-component/
├── src/
│   └── component.py          # Main component code
├── tests/
│   └── test_component.py
├── Dockerfile
├── component_config/
│   └── component.json        # Configuration schema
└── data/                     # Local testing data
    ├── in/
    │   └── tables/
    │       └── source.csv
    └── out/
        └── tables/
            └── result.csv
```

### Basic Component Code

```python
# src/component.py
from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
import csv

class Component(ComponentBase):
    """
    Custom Python component that processes data from Storage.
    """

    def run(self):
        """Main execution method."""
        # Get parameters from configuration
        params = self.configuration.parameters
        multiply_by = params.get('multiply_by', 1)

        # Access input tables
        input_tables = self.get_input_tables_definitions()
        if not input_tables:
            raise UserException("No input tables provided")

        # Process first input table
        input_table = input_tables[0]
        output_table = self.create_out_table_definition(
            'result.csv',
            primary_key=['id']
        )

        # Read and process data
        with open(input_table.full_path, 'r') as infile, \
             open(output_table.full_path, 'w', newline='') as outfile:

            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Process row
                if 'value' in row:
                    row['value'] = str(int(row['value']) * multiply_by)
                writer.writerow(row)

        # Write manifest (handles metadata)
        self.write_manifests()

        self.logger.info("Processing complete")


if __name__ == "__main__":
    try:
        comp = Component()
        comp.run()
    except UserException as e:
        comp.logger.error(str(e))
        exit(1)
    except Exception as e:
        comp.logger.exception(str(e))
        exit(2)
```

### Configuration Schema

```json
{
  "type": "object",
  "title": "Parameters",
  "required": ["multiply_by"],
  "properties": {
    "multiply_by": {
      "type": "integer",
      "title": "Multiply By",
      "description": "Factor to multiply values by",
      "default": 1
    }
  }
}
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ /code/src/

CMD ["python", "-u", "/code/src/component.py"]
```

### requirements.txt

```
keboola.component>=1.6.0
```

## Local Development

### Setup Data Folder

```bash
mkdir -p data/in/tables data/out/tables
```

### Create config.json

```json
{
  "parameters": {
    "multiply_by": 10
  },
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-main.source",
          "destination": "source.csv"
        }
      ]
    },
    "output": {
      "tables": [
        {
          "source": "result.csv",
          "destination": "in.c-main.result"
        }
      ]
    }
  }
}
```

### Run Locally

```bash
# Using Docker
docker build -t my-component .
docker run --rm \
  -v $(pwd)/data:/data \
  -e KBC_DATADIR=/data \
  my-component

# Or directly with Python
export KBC_DATADIR=./data
python src/component.py
```

## Input/Output Mapping

### Reading Input Tables

```python
# Get all input tables
input_tables = self.get_input_tables_definitions()

for table in input_tables:
    print(f"Table: {table.name}")
    print(f"Path: {table.full_path}")
    print(f"Columns: {table.columns}")

    # Read CSV data
    with open(table.full_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Process row
            pass
```

### Writing Output Tables

```python
# Create output table definition
output_table = self.create_out_table_definition(
    'output.csv',
    primary_key=['id'],
    incremental=False,
    delete_where=None
)

# Write data
with open(output_table.full_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'value'])
    writer.writeheader()
    writer.writerow({'id': '1', 'value': '100'})

# Write manifest (required!)
self.write_manifests()
```

## State Management

### Reading Previous State

```python
def run(self):
    # Get state from previous run
    state = self.get_state_file()
    last_processed = state.get('last_id', 0)

    self.logger.info(f"Last processed ID: {last_processed}")

    # Process only new records
    # ...

    # Save new state
    self.write_state_file({
        'last_id': new_last_id,
        'processed_at': datetime.now().isoformat()
    })
```

## Deployment to Keboola

### 1. Create GitHub Repository

```bash
gh repo create my-component --public
git init
git add .
git commit -m "Initial component"
git push -u origin main
```

### 2. Register in Developer Portal

Use the Developer Portal API or UI:

```python
import requests

vendor_token = os.environ['KEBOOLA_VENDOR_TOKEN']

response = requests.post(
    'https://connection.keboola.com/v2/storage/dev-branches',
    headers={'X-StorageApi-Token': vendor_token},
    json={
        'name': 'my-component',
        'type': 'python',
        'repository': 'https://github.com/username/my-component',
        'tag': 'main'
    }
)
```

### 3. Configure CI/CD

Add GitHub Actions for automatic deployment:

```yaml
# .github/workflows/deploy.yml
name: Deploy Component
on:
  push:
    tags:
      - '*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Push
        run: |
          docker build -t my-component:${{ github.ref_name }} .
          docker push my-component:${{ github.ref_name }}
```

## Best Practices

### Error Handling

```python
from keboola.component.exceptions import UserException

# User errors (configuration, data issues)
if not params.get('required_field'):
    raise UserException("Missing required parameter: required_field")

# System errors (let them bubble up)
try:
    result = api_call()
except Exception as e:
    # This will be caught by the framework
    raise
```

### Logging

```python
# Use component logger
self.logger.info("Processing started")
self.logger.warning("Missing optional field")
self.logger.error("Failed to process row", extra={'row_id': row_id})
```

### CSV Processing

```python
import csv

# Always use csv module, not pandas (for memory efficiency)
with open(input_path, 'r') as infile:
    reader = csv.DictReader(infile)

    # Process in chunks for large files
    chunk = []
    for row in reader:
        chunk.append(row)
        if len(chunk) >= 10000:
            process_chunk(chunk)
            chunk = []

    # Process remaining
    if chunk:
        process_chunk(chunk)
```

## When to Use Components vs Direct API

### Use Custom Python Components when:
- Building production workflows
- Need scheduled/orchestrated runs
- Want version control and CI/CD
- Sharing with team/organization
- Need state management

### Use Direct Storage API when:
- One-off scripts
- External systems integration
- Quick data exploration
- Not running within Keboola infrastructure

## Additional Resources

- **Component Developer Documentation**: See `claude/component-developer/` for detailed guides
- **Cookiecutter Template**: `gh:keboola/cookiecutter-python-component`
- **Example Components**: https://github.com/keboola/component-examples
- **Developer Portal**: https://components.keboola.com
