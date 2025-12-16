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
import time
import requests

# Start async table export (NOTE: Uses POST, not GET)
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll for completion with timeout and error handling
timeout = 300  # 5 minutes
start_time = time.time()

while time.time() - start_time < timeout:
    try:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token},
            timeout=30
        )
        job_response.raise_for_status()
        job = job_response.json()

        if job["status"] == "success":
            # Download and save to file
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            data_response.raise_for_status()

            # Save to local file
            with open("output.csv", "wb") as f:
                f.write(data_response.content)
            
            print(f"Table exported to output.csv")
            break

        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job {job['status']}: {error_msg}")

        # Job still processing
        time.sleep(2)

    except requests.exceptions.Timeout:
        print("Request timed out, retrying...")
        time.sleep(5)
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}, retrying...")
        time.sleep(5)
else:
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
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


## 6. Using Wrong HTTP Methods

**Problem**: Using GET instead of POST for async operations

**Solution**: Always use POST for async export endpoints:

```python
# ❌ WRONG - This will fail with 405 Method Not Allowed
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

# ✅ CORRECT - Async exports require POST
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
```

**Key endpoints requiring POST**:
- `/v2/storage/tables/{id}/export-async` - Export table data
- `/v2/storage/buckets/{id}/tables-async` - Create table
- `/v2/storage/tables/{id}/import-async` - Import data

## 7. Incomplete Job Status Handling

**Problem**: Only checking for "success" and "error" statuses

**Solution**: Handle all possible job states:

```python
def wait_for_job(job_id, timeout=300):
    """Wait for job completion with proper state handling."""
    start = time.time()

    while time.time() - start < timeout:
        try:
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=30
            )
            response.raise_for_status()
            job = response.json()

            # Success state
            if job["status"] == "success":
                return job

            # Failure states - all should raise exceptions
            elif job["status"] in ["error", "cancelled", "terminated"]:
                error_msg = job.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Job {job['status']}: {error_msg}")

            # Still processing: waiting, processing
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"Network error polling job: {e}")
            time.sleep(5)

    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")
```

**Possible job statuses**:
- `waiting` - Job queued
- `processing` - Job running
- `success` - Job completed successfully
- `error` - Job failed with error
- `cancelled` - Job was cancelled
- `terminated` - Job was terminated



### Recommended: Reusable Export Function

For production use, wrap the export logic in a reusable function:

```python
import time
import requests
from typing import Optional

def export_table_to_file(
    table_id: str,
    output_file: str,
    stack_url: str,
    token: str,
    timeout: int = 300
) -> None:
    """Export Keboola table to local CSV file.
    
    Args:
        table_id: Table ID (e.g., 'in.c-main.customers')
        output_file: Path to save CSV file
        stack_url: Keboola stack URL
        token: Storage API token
        timeout: Max seconds to wait for job completion
        
    Raises:
        Exception: If job fails or is cancelled
        TimeoutError: If job doesn't complete in time
        requests.exceptions.RequestException: On network errors
    """
    # Start export job
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
        try:
            job_response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=30
            )
            job_response.raise_for_status()
            job = job_response.json()
            
            if job["status"] == "success":
                # Download file
                file_url = job["results"]["file"]["url"]
                data_response = requests.get(file_url, timeout=60)
                data_response.raise_for_status()
                
                # Save to file
                with open(output_file, "wb") as f:
                    f.write(data_response.content)
                
                print(f"Table exported to {output_file}")
                return
                
            elif job["status"] in ["error", "cancelled", "terminated"]:
                error_msg = job.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Job {job['status']}: {error_msg}")
            
            # Still processing
            time.sleep(2)
            
        except requests.exceptions.Timeout:
            print("Request timed out, retrying...")
            time.sleep(5)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

# Usage example
export_table_to_file(
    table_id="in.c-main.customers",
    output_file="customers.csv",
    stack_url=os.environ["KEBOOLA_STACK_URL"],
    token=os.environ["KEBOOLA_TOKEN"]
)
```

