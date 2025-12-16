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

### Import Data to Existing Table

```python
# Import data to an existing table (replaces all data)
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "dataString": csv_data
    }
)

job_id = response.json()["id"]
# Poll job until completion
```

### Create Table with Primary Key

```python
# Create table with primary key defined
csv_data = "id,name,value\n1,foo,100\n2,bar,200"

response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "name": "my_table",
        "primaryKey": "id",  # Define primary key
        "dataString": csv_data
    }
)
```

### Incremental Write (Upsert)

```python
# Import data incrementally (upsert based on primary key)
# Primary key MUST be defined on the table first
csv_data = "id,name,value\n1,foo,150\n3,baz,300"

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "incremental": "1",  # Enable incremental mode
        "dataString": csv_data
    }
)

# This will:
# - Update row with id=1 (foo,150)
# - Keep row with id=2 unchanged
# - Insert new row with id=3 (baz,300)
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

#### Reading Data Incrementally

Use changedSince parameter to export only changed rows:

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

#### Writing Data Incrementally

Use incremental parameter to upsert data based on primary key:

```python
# IMPORTANT: Table must have primary key defined
# Incremental import will:
# - INSERT new rows (primary key doesn't exist)
# - UPDATE existing rows (primary key matches)
# - KEEP unchanged rows (primary key not in import data)

csv_data = "id,name,updated_at\n1,Alice,2024-01-15\n5,Eve,2024-01-15"

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "incremental": "1"  # Must be "1" or "true"
    }
)

job_id = response.json()["id"]
# Poll job until completion
```

#### Common Incremental Write Pattern

```python
def upsert_data_to_keboola(table_id, csv_data):
    """Upsert data to Keboola table with proper error handling."""
    
    # Check if table has primary key
    table_info = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}",
        headers={"X-StorageApi-Token": token}
    ).json()
    
    if not table_info.get("primaryKey"):
        raise ValueError(
            f"Table {table_id} has no primary key. "
            f"Primary key is required for incremental loads."
        )
    
    # Import incrementally
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={
            "X-StorageApi-Token": token,
            "Content-Type": "text/csv"
        },
        params={
            "incremental": "1",
            "dataString": csv_data
        }
    )
    
    # Wait for completion
    job_id = response.json()["id"]
    return wait_for_job(job_id)
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

## 6. Missing Primary Keys for Incremental Loads

**Problem**: Attempting incremental import without primary key defined

**Solution**: Always define primary key when creating tables for incremental use:

```python
# ❌ WRONG - Creating table without primary key, then trying incremental
requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    params={"name": "my_table", "dataString": csv_data}
)

# Later: This will FAIL
requests.post(
    f"https://{stack_url}/v2/storage/tables/in.c-main.my_table/import-async",
    params={"incremental": "1", "dataString": new_data}
)
# Error: "Primary key required for incremental import"

# ✅ CORRECT - Define primary key at creation
requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    params={
        "name": "my_table",
        "primaryKey": "id",  # or "primaryKey[]": ["id", "date"] for composite
        "dataString": csv_data
    }
)

# Now incremental imports work
requests.post(
    f"https://{stack_url}/v2/storage/tables/in.c-main.my_table/import-async",
    params={"incremental": "1", "dataString": new_data}
)
```

## 7. Confusing Table Creation vs Import Endpoints

**Problem**: Using wrong endpoint for the operation

**Solution**: Understand the difference:

```python
# CREATE new table (use bucket endpoint)
# URL: /v2/storage/buckets/{bucket_id}/tables-async
response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    params={
        "name": "new_table",  # Just table name, not full ID
        "dataString": csv_data
    }
)
# Creates: in.c-main.new_table

# IMPORT to existing table (use table endpoint)
# URL: /v2/storage/tables/{table_id}/import-async
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/in.c-main.new_table/import-async",
    params={
        "incremental": "0",  # 0 = replace, 1 = upsert
        "dataString": csv_data
    }
)

# Helper function to handle both cases
def write_to_storage(bucket_id, table_name, csv_data, incremental=False):
    """Write data to Storage, creating table if needed."""
    table_id = f"{bucket_id}.{table_name}"
    
    # Check if table exists
    check = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}",
        headers={"X-StorageApi-Token": token}
    )
    
    if check.status_code == 404:
        # Create new table
        response = requests.post(
            f"https://{stack_url}/v2/storage/buckets/{bucket_id}/tables-async",
            headers={"X-StorageApi-Token": token},
            params={
                "name": table_name,
                "primaryKey": "id",  # Set if using incremental later
                "dataString": csv_data
            }
        )
    else:
        # Import to existing table
        response = requests.post(
            f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
            headers={"X-StorageApi-Token": token},
            params={
                "incremental": "1" if incremental else "0",
                "dataString": csv_data
            }
        )
    
    return response.json()["id"]  # Job ID
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