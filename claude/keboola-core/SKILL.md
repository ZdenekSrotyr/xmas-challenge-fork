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
import requests
import time
import os

# Initiate table export (requires POST, not GET)
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll for completion with proper error handling
max_attempts = 150  # 5 minutes with 2-second intervals
attempt = 0

while attempt < max_attempts:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()

    job = job_response.json()
    
    if job["status"] == "success":
        break
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Job {job_id} failed with status '{job['status']}': {error_msg}")
    
    time.sleep(2)
    attempt += 1

if attempt >= max_attempts:
    raise TimeoutError(f"Job {job_id} did not complete within timeout")

# Download exported file
if job["status"] == "success":
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url)
    data_response.raise_for_status()
    
    # Save to local file
    output_file = "exported_table.csv"
    with open(output_file, "wb") as f:
        f.write(data_response.content)
    
    print(f"Table exported successfully to {output_file}")
    
    # Optional: Load into memory if needed
    # import csv
    # import io
    # reader = csv.DictReader(io.StringIO(data_response.text))
    # data = list(reader)
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
def wait_for_job(job_id, timeout=300, poll_interval=2):
    """Wait for job completion with timeout and comprehensive error handling.
    
    Args:
        job_id: Keboola job ID
        timeout: Maximum time to wait in seconds
        poll_interval: Seconds between status checks
        
    Returns:
        dict: Job details on success
        
    Raises:
        Exception: If job fails, is cancelled, or terminated
        TimeoutError: If job doesn't complete within timeout
    """
    start = time.time()

    while time.time() - start < timeout:
        try:
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to check job status: {e}")
            time.sleep(poll_interval)
            continue

        job = response.json()

        if job["status"] == "success":
            return job
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(
                f"Job {job_id} failed with status '{job['status']}': {error_msg}"
            )
        # Job is still processing (status: waiting, processing)
        time.sleep(poll_interval)

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


## 6. Wrong HTTP Method for Async Operations

**Problem**: Using GET instead of POST for async export endpoints

**Solution**: Always use POST for export-async endpoints:

```python
# ❌ WRONG - This will fail with 405 Method Not Allowed
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

# ✅ CORRECT - Use POST for async operations
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()
```

**Rule of thumb**: Endpoints ending in `-async` typically require POST to initiate the job.



### Complete Example: Export and Save Table

Here's a complete, production-ready example for exporting a table to a local file:

```python
import requests
import time
import os
from typing import Optional

def export_table_to_file(
    table_id: str,
    output_file: str,
    stack_url: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    """Export a Keboola table to a local CSV file.
    
    Args:
        table_id: Table ID (e.g., 'in.c-main.customers')
        output_file: Local file path for output
        stack_url: Keboola stack URL (defaults to env var)
        token: Storage API token (defaults to env var)
        
    Returns:
        str: Path to exported file
        
    Raises:
        ValueError: If table_id format is invalid
        Exception: If export fails
        TimeoutError: If export doesn't complete
    """
    # Get credentials from environment if not provided
    stack_url = stack_url or os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
    token = token or os.environ["KEBOOLA_TOKEN"]
    
    headers = {"X-StorageApi-Token": token}
    
    # Validate table ID format
    import re
    if not re.match(r'^(in|out)\.c-[a-z0-9-]+\.[a-z0-9_-]+$', table_id):
        raise ValueError(f"Invalid table ID format: {table_id}")
    
    # Step 1: Initiate export (POST required)
    print(f"Initiating export of {table_id}...")
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers=headers
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    print(f"Export job started: {job_id}")
    
    # Step 2: Poll for completion
    print("Waiting for export to complete...")
    max_attempts = 150  # 5 minutes
    attempt = 0
    
    while attempt < max_attempts:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers=headers
        )
        job_response.raise_for_status()
        job = job_response.json()
        
        if job["status"] == "success":
            print("Export completed successfully")
            break
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Export failed: {error_msg}")
        
        time.sleep(2)
        attempt += 1
    
    if attempt >= max_attempts:
        raise TimeoutError(f"Export did not complete within 5 minutes")
    
    # Step 3: Download file
    print(f"Downloading to {output_file}...")
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url)
    data_response.raise_for_status()
    
    with open(output_file, "wb") as f:
        f.write(data_response.content)
    
    file_size = os.path.getsize(output_file)
    print(f"Successfully exported {file_size:,} bytes to {output_file}")
    
    return output_file

# Usage example
if __name__ == "__main__":
    export_table_to_file(
        table_id="in.c-main.customers",
        output_file="customers.csv"
    )
```

