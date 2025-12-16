# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/`
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-16T14:06:01.482382

---

## Overview

This skill provides comprehensive knowledge about the Keboola platform,
including API usage, best practices, and common pitfalls.

**When to activate this skill:**
- User asks about Keboola Storage API
- User needs help with Keboola Jobs API
- User asks about regional stacks or Stack URLs
- User encounters Keboola-related errors

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

## Access Methods

There are multiple ways to interact with Keboola:

### MCP Server (Model Context Protocol)
A Claude AI integration providing high-level tools for data exploration:
- Best for: Interactive data exploration, prototyping, validation
- Authentication: OAuth (one-time setup)
- Data limits: Suitable for tables under ~1000 rows
- See `04-mcp-vs-api.md` for detailed guidance

### Storage API
Direct HTTP REST API for programmatic access:
- Best for: Production pipelines, large datasets, automated workflows
- Authentication: API token per request
- Data limits: No limits (supports pagination)
- See `02-storage-api.md` for implementation details

### Components
Platform-managed data processing modules:
- Best for: Scheduled workflows, complex transformations, external integrations
- Authentication: Managed by platform
- See component developer documentation

**Need help choosing?** See `04-mcp-vs-api.md` for a complete comparison and decision framework.


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
import time

# Start async export job (NOTE: POST method required)
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll for completion with timeout
timeout = 300  # 5 minutes
start_time = time.time()

while time.time() - start_time < timeout:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()

    job = job_response.json()
    
    if job["status"] == "success":
        # Download and save data to file
        file_url = job["results"]["file"]["url"]
        data_response = requests.get(file_url)
        
        with open("table_data.csv", "wb") as f:
            f.write(data_response.content)
        
        print(f"Table exported to table_data.csv")
        break
    
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Export job failed with status {job['status']}: {error_msg}")
    
    time.sleep(2)
else:
    raise TimeoutError(f"Export job {job_id} did not complete within {timeout} seconds")

# Optional: Load data into memory if needed
import csv
with open("table_data.csv", "r") as f:
    reader = csv.DictReader(f)
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


### Export Table to File (Complete Example)

For a complete, production-ready example that saves data to a file:

```python
import requests
import os
import time

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]
table_id = "in.c-main.customers"
output_file = "customers.csv"

def export_table_to_file(table_id, output_file, timeout=300):
    """Export Keboola table to local CSV file."""
    
    # Start async export
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    print(f"Export job started: {job_id}")
    
    # Poll for completion
    start_time = time.time()
    while time.time() - start_time < timeout:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        job_response.raise_for_status()
        job = job_response.json()
        
        if job["status"] == "success":
            # Download file
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            with open(output_file, "wb") as f:
                f.write(data_response.content)
            
            print(f"Table exported to {output_file}")
            return output_file
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job {job['status']}: {error_msg}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Export did not complete within {timeout}s")

# Usage
export_table_to_file(table_id, output_file)
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
        response.raise_for_status()

        job = response.json()

        if job["status"] == "success":
            return job
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job failed with status {job['status']}: {error_msg}")

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


## 3. Wrong HTTP Method for Async Endpoints

**Problem**: Using GET instead of POST for async export operations

**Solution**: Always use POST for /export-async endpoints:

```python
# ❌ WRONG - This will return 405 Method Not Allowed
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

# ✅ CORRECT - Use POST to initiate async jobs
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
```

**Why**: The `/export-async` endpoint creates a new export job, which is a write operation requiring POST. The API will reject GET requests.



---

## Metadata

```json
{
  "generated_at": "2025-12-16T14:06:01.482382",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0"
}
```

---

**End of Skill**