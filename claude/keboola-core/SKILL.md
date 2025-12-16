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

# Start async export job (IMPORTANT: Must use POST, not GET)
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll for completion with timeout
start_time = time.time()
timeout = 300  # 5 minutes

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
            break
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job failed with status {job['status']}: {error_msg}")
        
        time.sleep(2)
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during polling: {e}")
        time.sleep(5)  # Wait longer on network errors
        continue

if time.time() - start_time >= timeout:
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

# Download data to file
if job["status"] == "success":
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url, timeout=60)
    data_response.raise_for_status()
    
    # Save to local file
    output_path = f"{table_id.replace('.', '_')}.csv"
    with open(output_path, 'wb') as f:
        f.write(data_response.content)
    
    print(f"Table exported to {output_path}")
    
    # Or load into memory if needed
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
    """Wait for job completion with timeout and complete error handling."""
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
            status = job["status"]

            if status == "success":
                return job
            elif status in ["error", "cancelled", "terminated"]:
                error_msg = job.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Job failed with status '{status}': {error_msg}")

            time.sleep(2)
            
        except requests.exceptions.Timeout:
            print(f"Timeout polling job {job_id}, retrying...")
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as e:
            print(f"Network error polling job {job_id}: {e}")
            time.sleep(5)
            continue

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

**Solution**: Always use POST to initiate async operations:

```python
# ❌ WRONG - This will fail with 405 Method Not Allowed
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

# ✅ CORRECT - Use POST to start async jobs
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)
```

**Rule of thumb**: Any endpoint ending in `-async` requires POST to initiate the operation.

## 7. Incomplete Job Status Handling

**Problem**: Only checking for "success" and "error" statuses

**Solution**: Handle all possible job statuses:

```python
def wait_for_job(job_id, timeout=300):
    """Wait for job completion with complete status handling."""
    start = time.time()

    while time.time() - start < timeout:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token},
            timeout=30
        )
        response.raise_for_status()
        
        job = response.json()
        status = job["status"]
        
        # Success - job completed
        if status == "success":
            return job
        
        # Failure statuses - raise exception
        elif status in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job {job_id} failed with status '{status}': {error_msg}")
        
        # Still processing - continue waiting
        elif status in ["waiting", "processing"]:
            time.sleep(2)
        
        else:
            # Unknown status - log and continue
            print(f"Warning: Unknown job status '{status}'")
            time.sleep(2)

    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")
```

**Possible job statuses**:
- `waiting` - Job is queued
- `processing` - Job is running
- `success` - Job completed successfully
- `error` - Job failed with an error
- `cancelled` - Job was cancelled by user
- `terminated` - Job was terminated by system


### Quick Reference: Table Export

**Endpoint**: `POST /v2/storage/tables/{tableId}/export-async`

**Common Parameters**:
- `changedSince`: ISO 8601 timestamp for incremental exports
- `whereColumn`: Column name for filtering
- `whereValues`: Array of values to filter by
- `limit`: Maximum number of rows to export

**Job Statuses**:
- ✅ `success` - Export completed, download from `results.file.url`
- ⏳ `waiting`, `processing` - Still running, continue polling
- ❌ `error`, `cancelled`, `terminated` - Failed, check `error.message`

**Complete Example**:
```python
import requests
import time

def export_table_to_file(table_id, output_path, timeout=300):
    """Export Keboola table to local CSV file."""
    
    # 1. Start export job (POST, not GET!)
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # 2. Poll until complete
    start = time.time()
    while time.time() - start < timeout:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        job = job_response.json()
        
        if job["status"] == "success":
            break
        elif job["status"] in ["error", "cancelled", "terminated"]:
            raise Exception(f"Export failed: {job.get('error', {}).get('message')}")
        
        time.sleep(2)
    
    # 3. Download file
    file_url = job["results"]["file"]["url"]
    data = requests.get(file_url)
    
    with open(output_path, 'wb') as f:
        f.write(data.content)
    
    return output_path

# Usage
export_table_to_file("in.c-main.customers", "customers.csv")
```
