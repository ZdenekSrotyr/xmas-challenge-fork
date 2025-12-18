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
### Create New Table from CSV

```python
# Upload CSV file to create a NEW table
csv_data = "id,name,value\n1,foo,100\n2,bar,200"

response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "name": "my_table",
        "primaryKey": "id",  # Optional: set primary key
        "dataString": csv_data
    }
)
response.raise_for_status()

job_id = response.json()["id"]
# Poll job until completion (see export example above)
```

### Import Data to Existing Table

```python
# Import data to an EXISTING table
table_id = "in.c-main.my_table"
csv_data = "id,name,value\n3,baz,300\n4,qux,400"

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
response.raise_for_status()

job_id = response.json()["id"]
# Poll job until completion
```

### Incremental Loads (Append/Update Data)

**Important**: Incremental loads require the table to have a primary key defined.

```python
# Incremental load: append new rows or update existing rows by primary key
table_id = "in.c-main.my_table"
csv_data = "id,name,value\n1,foo_updated,150\n5,new_row,500"

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
response.raise_for_status()

job_id = response.json()["id"]
# Poll job until completion
```

**How incremental mode works**:
- If a row with the same primary key exists, it gets UPDATED
- If a row with a new primary key exists, it gets APPENDED
- Existing rows not in the import data are NOT deleted

### Set or Change Primary Key

```python
# Set primary key on existing table
table_id = "in.c-main.my_table"

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "primaryKey": ["id"]  # Can be multiple columns: ["id", "date"]
    }
)
response.raise_for_status()
```
```

## Common Patterns

### Pagination

Keboola Storage API supports pagination for listing resources and previewing data. Choose the appropriate method based on your use case.

#### Overview

| Use Case | Method | Max Results | Best For |
|----------|--------|-------------|----------|
| List tables/buckets | `limit`/`offset` params | Unlimited | Browsing metadata |
| Quick data preview | `data-preview` endpoint | 1,000 rows | Small samples |
| Full table export | `export-async` endpoint | Unlimited | Production data export |

#### Data Preview Pagination

For quick data preview with small result sets, use limit/offset pagination:

```python
def export_table_paginated(table_id, chunk_size=10000):
    """Export table preview in chunks using limit/offset."""
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
        response.raise_for_status()

        chunk = response.json()
        if not chunk:
            break

        all_data.extend(chunk)
        offset += chunk_size

    return all_data
```

**Note**: `data-preview` endpoint is limited to 1000 rows maximum. For larger datasets, use async export.

#### API Response Pagination (List Operations)

Many API endpoints that return lists support pagination parameters. Use this for browsing tables, buckets, configurations, and other metadata.

**Endpoints that support pagination:**
- `/v2/storage/tables` - List all tables
- `/v2/storage/buckets` - List all buckets
- `/v2/storage/files` - List files
- `/v2/storage/jobs` - List jobs
- `/v2/storage/events` - List events

**Basic pagination example:**

```python
def list_all_tables_paginated():
    """List all tables with pagination support."""
    all_tables = []
    offset = 0
    limit = 100  # Request 100 records per page

    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tables",
            headers={"X-StorageApi-Token": token},
            params={
                "limit": limit,
                "offset": offset
            }
        )
        response.raise_for_status()

        tables = response.json()
        if not tables:
            break

        all_tables.extend(tables)
        
        # If fewer results than limit, we've reached the end
        if len(tables) < limit:
            break
            
        offset += limit

    return all_tables
```

**Pagination with filtering:**

```python
def list_tables_in_bucket_paginated(bucket_id):
    """List tables in specific bucket with pagination."""
    all_tables = []
    offset = 0
    limit = 50

    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/buckets/{bucket_id}/tables",
            headers={"X-StorageApi-Token": token},
            params={
                "limit": limit,
                "offset": offset
            }
        )
        response.raise_for_status()

        tables = response.json()
        if not tables or len(tables) < limit:
            all_tables.extend(tables)
            break
            
        all_tables.extend(tables)
        offset += limit

    return all_tables
```

#### Pagination Parameters

Common pagination parameters across Keboola Storage API:

- **limit**: Number of records to return per request
  - Default: 100 (varies by endpoint)
  - Maximum: 1000 for most endpoints
  - Recommended: 100-500 for optimal performance
- **offset**: Number of records to skip from the beginning
  - Default: 0
  - Use case: Skip to specific page (e.g., offset=200 for page 3 with limit=100)

**Example parameters:**

```python
# Get first page (records 1-100)
params = {
    "limit": 100,
    "offset": 0
}

# Get second page (records 101-200)
params = {
    "limit": 100,
    "offset": 100
}

# Get third page (records 201-300)
params = {
    "limit": 100,
    "offset": 200
}
```

**Calculate pagination:**

```python
def get_page_params(page_number, page_size=100):
    """Calculate offset for given page number (1-indexed)."""
    return {
        "limit": page_size,
        "offset": (page_number - 1) * page_size
    }

# Usage
page_1 = get_page_params(1, 100)  # {"limit": 100, "offset": 0}
page_2 = get_page_params(2, 100)  # {"limit": 100, "offset": 100}
page_5 = get_page_params(5, 50)   # {"limit": 50, "offset": 200}
```

#### Full Table Export (Recommended for Large Tables)

For exporting complete tables, especially large ones, use async export instead of pagination:

```python
def export_large_table(table_id):
    """Export large table using async job (handles pagination internally)."""
    # Start async export
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # Poll for completion
    import time
    timeout = 600
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        job_response.raise_for_status()
        job = job_response.json()
        
        if job["status"] == "success":
            # Download complete file (pagination handled by Keboola)
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            with open("table_export.csv", "wb") as f:
                f.write(data_response.content)
            
            return "table_export.csv"
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Export failed: {error_msg}")
        
        time.sleep(2)
    
    raise TimeoutError("Export job timeout")
```

**When to use each approach**:

- **data-preview with pagination**: Quick checks, small datasets (<1000 rows), development/debugging
- **List endpoints with pagination**: Browsing tables, buckets, configurations, metadata operations
- **Async export**: Production data export, large tables (>1000 rows), complete data downloads

**Performance considerations:**

```python
# For small previews (< 1000 rows): data-preview is fastest
def quick_preview(table_id, rows=100):
    response = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}/data-preview",
        headers={"X-StorageApi-Token": token},
        params={"limit": rows}
    )
    return response.json()

# For listing metadata: pagination is efficient
def list_all_tables():
    # Uses pagination internally (see example above)
    return list_all_tables_paginated()

# For large datasets: async export handles pagination automatically
def export_full_table(table_id):
    # Keboola handles pagination internally, returns complete file
    return export_large_table_correct(table_id)
```

### Reading Data Incrementally

Use changedSince parameter to export only recently modified data:

```python
from datetime import datetime, timedelta

# Get data changed in last 24 hours
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token},
    params={"changedSince": yesterday}
)
response.raise_for_status()

job_id = response.json()["id"]
# Poll job until completion
```

### Writing Data Incrementally

See the "Incremental Loads (Append/Update Data)" section under "Writing Tables" above for how to write data incrementally using `incremental: "1"` parameter.


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


## Storage vs Workspace Context

### Understanding the Difference

**Storage API** operates at the **project level**:
- Uses project-wide Storage API token
- Manages permanent data storage
- Uses table IDs like `in.c-main.customers`
- Accessed via REST API endpoints
- Used for: data ingestion, component development, orchestration

**Workspace** operates at the **workspace level**:
- Uses workspace-specific database credentials
- Provides temporary SQL access to project data
- Uses qualified names like `"PROJECT_ID"."in.c-main"."customers"`
- Accessed via native database connections (JDBC/ODBC)
- Used for: Data Apps, transformations, SQL analysis

### When to Use Storage API (Project Context)

✅ **Use Storage API when**:
- Developing custom components
- Running scripts outside Keboola
- Managing buckets and tables
- Orchestrating data pipelines
- Local development/testing

```python
# Example: Local development script
import os
import requests

token = os.environ['KEBOOLA_TOKEN']
stack_url = os.environ.get('KEBOOLA_STACK_URL', 'connection.keboola.com')

# Project-level API call
response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": token}
)

tables = response.json()
for table in tables:
    print(f"Project table: {table['id']}")
```

### When to Use Workspace (Workspace Context)

✅ **Use Workspace when**:
- Building Data Apps (production runtime)
- Writing SQL transformations
- Running queries in Snowflake/Redshift workspace
- Need direct database performance

```python
# Example: Data App in production
import os
import streamlit as st

if 'KBC_PROJECT_ID' in os.environ:
    # Running in workspace - use direct connection
    conn = st.connection('snowflake', type='snowflake')
    
    # Workspace-level SQL query with qualified names
    project_id = os.environ['KBC_PROJECT_ID']
    query = f'''
        SELECT * 
        FROM "{project_id}"."in.c-main"."customers"
        WHERE "status" = 'active'
    '''
    df = conn.query(query)
else:
    # Local development - use Storage API
    # (see Storage API examples above)
    pass
```

### Hybrid Pattern: Support Both Contexts

Data Apps should support both contexts for local development and production:

```python
# utils/data_loader.py
import os
import streamlit as st
import requests

def get_connection_mode():
    """Detect runtime environment."""
    return 'workspace' if 'KBC_PROJECT_ID' in os.environ else 'storage_api'

@st.cache_resource
def get_connection():
    """Get appropriate connection for environment."""
    mode = get_connection_mode()
    
    if mode == 'workspace':
        # Production: Use workspace connection
        return st.connection('snowflake', type='snowflake')
    else:
        # Local: Return Storage API client
        return StorageAPIClient(
            token=os.environ['KEBOOLA_TOKEN'],
            stack_url=os.environ.get('KEBOOLA_STACK_URL')
        )

def get_table_reference(bucket_id, table_name):
    """Get correct table reference for environment."""
    mode = get_connection_mode()
    
    if mode == 'workspace':
        # Workspace: Fully qualified name
        project_id = os.environ['KBC_PROJECT_ID']
        return f'"{project_id}"."{bucket_id}"."{table_name}"'
    else:
        # Storage API: bucket.table format
        return f"{bucket_id}.{table_name}"

# Usage in Data App
@st.cache_data(ttl=300)
def load_customers():
    conn = get_connection()
    table_ref = get_table_reference('in.c-main', 'customers')
    
    if get_connection_mode() == 'workspace':
        query = f'SELECT * FROM {table_ref}'
        return conn.query(query)
    else:
        # Use Storage API export
        return conn.export_table(table_ref)
```

### Common Pitfalls

❌ **Don't mix contexts**:
```python
# WRONG: Using Storage API table ID in workspace SQL
query = f"SELECT * FROM in.c-main.customers"  # Fails in workspace

# CORRECT: Use qualified names in workspace
query = f'SELECT * FROM "{project_id}"."in.c-main"."customers"'
```

❌ **Don't use workspace credentials in Storage API**:
```python
# WRONG: Workspace connection for Storage API call
conn = st.connection('snowflake')  # This is workspace, not Storage API

# CORRECT: Use Storage API token
import requests
response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": storage_token}
)
```

## Batch Operations

Batch operations allow you to work with multiple tables efficiently, reducing overhead and improving performance for bulk data transfers.

### Prerequisites

Before using batch operations, ensure you have the required imports and variables set up:

```python
import requests
import os
import time
import csv
from typing import List, Dict, Any

# Initialize connection variables
stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

# Verify authentication
response = requests.get(
    f"https://{stack_url}/v2/storage/tokens/verify",
    headers={"X-StorageApi-Token": token}
)
response.raise_for_status()
print(f"Authenticated as: {response.json()['description']}")
```

### Helper Functions

#### Job Polling Helper

Reusable function for polling async jobs with proper error handling:

```python
def poll_job_until_complete(job_id: str, timeout: int = 600, poll_interval: int = 3) -> Dict[str, Any]:
    """
    Poll Keboola job until completion.
    
    Args:
        job_id: Keboola job ID to monitor
        timeout: Maximum wait time in seconds (default 10 minutes)
        poll_interval: Seconds between status checks (minimum 2 seconds)
    
    Returns:
        Job result dictionary on success
    
    Raises:
        TimeoutError: Job didn't complete within timeout
        Exception: Job failed with error
    """
    if poll_interval < 2:
        raise ValueError("poll_interval must be at least 2 seconds to avoid rate limits")
    
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < timeout:
        attempts += 1
        
        try:
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempts}): {e}")
            time.sleep(min(poll_interval * 2, 10))
            continue
        
        job = response.json()
        status = job["status"]
        
        if status == "success":
            print(f"Job {job_id} completed successfully")
            return job
        
        elif status in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job {job_id} failed with status '{status}': {error_msg}")
        
        elif status in ["waiting", "processing"]:
            elapsed = time.time() - start_time
            if attempts % 10 == 0:  # Log every 10th check
                print(f"Job {job_id} still {status} (elapsed: {elapsed:.1f}s)")
            time.sleep(poll_interval)
        
        else:
            print(f"Warning: Unknown job status '{status}' for job {job_id}")
            time.sleep(poll_interval)
    
    elapsed = time.time() - start_time
    raise TimeoutError(
        f"Job {job_id} did not complete within {timeout}s "
        f"(checked {attempts} times over {elapsed:.1f}s)"
    )
```

#### Export Helper with Retry

Wrapper for exporting single tables with built-in retry logic:

```python
def export_table(table_id: str, output_file: str = None, **params) -> str:
    """
    Export single table using async job.
    
    Args:
        table_id: Table ID (e.g., 'in.c-main.customers')
        output_file: Optional output filename (default: table_id.csv)
        **params: Additional export parameters (changedSince, whereColumn, etc.)
    
    Returns:
        Path to downloaded CSV file
    
    Raises:
        Exception: Export failed
    """
    if output_file is None:
        output_file = f"{table_id.replace('.', '_')}.csv"
    
    # Start async export
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token},
        params=params
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    print(f"Exporting {table_id} (job: {job_id})")
    
    # Poll for completion using helper
    job = poll_job_until_complete(job_id, timeout=600, poll_interval=3)
    
    # Download file
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url)
    data_response.raise_for_status()
    
    with open(output_file, "wb") as f:
        f.write(data_response.content)
    
    print(f"Exported {table_id} to {output_file}")
    return output_file


def export_table_with_retry(table_id: str, output_file: str = None, max_retries: int = 3, **params) -> str:
    """
    Export table with automatic retry on failure.
    
    Args:
        table_id: Table ID to export
        output_file: Optional output filename
        max_retries: Number of retry attempts (default: 3)
        **params: Additional export parameters
    
    Returns:
        Path to downloaded CSV file
    
    Raises:
        Exception: Export failed after all retries
    """
    for attempt in range(max_retries):
        try:
            return export_table(table_id, output_file, **params)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Export attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Export failed after {max_retries} attempts: {e}")
```

### Batch Export

Export multiple tables in parallel or sequence.

#### Sequential Export

Export tables one at a time (safer for many tables):

```python
def batch_export_tables_sequential(
    table_ids: List[str],
    output_dir: str = "exports",
    **export_params
) -> Dict[str, str]:
    """
    Export multiple tables sequentially.
    
    Args:
        table_ids: List of table IDs to export
        output_dir: Directory to save exported files (created if needed)
        **export_params: Additional parameters passed to each export
                        (changedSince, whereColumn, whereValues, whereOperator)
    
    Returns:
        Dictionary mapping table_id to output file path
    
    Example:
        results = batch_export_tables_sequential(
            ['in.c-main.customers', 'in.c-main.orders'],
            output_dir='data',
            changedSince='2024-01-01T00:00:00Z'
        )
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    failed = {}
    
    print(f"Starting batch export of {len(table_ids)} tables...")
    
    for i, table_id in enumerate(table_ids, 1):
        print(f"\n[{i}/{len(table_ids)}] Processing {table_id}")
        
        output_file = os.path.join(
            output_dir,
            f"{table_id.replace('.', '_')}.csv"
        )
        
        try:
            export_table_with_retry(table_id, output_file, **export_params)
            results[table_id] = output_file
        except Exception as e:
            print(f"Failed to export {table_id}: {e}")
            failed[table_id] = str(e)
    
    print(f"\n=== Batch Export Complete ===")
    print(f"Success: {len(results)}/{len(table_ids)} tables")
    if failed:
        print(f"Failed: {len(failed)} tables")
        for table_id, error in failed.items():
            print(f"  - {table_id}: {error}")
    
    if failed:
        raise Exception(f"Batch export completed with {len(failed)} failures")
    
    return results
```

#### Parallel Export (Advanced)

Export tables concurrently for faster processing:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_export_tables_parallel(
    table_ids: List[str],
    output_dir: str = "exports",
    max_workers: int = 5,
    **export_params
) -> Dict[str, str]:
    """
    Export multiple tables in parallel using thread pool.
    
    Args:
        table_ids: List of table IDs to export
        output_dir: Directory to save exported files
        max_workers: Maximum concurrent exports (default: 5, max recommended: 10)
        **export_params: Additional export parameters
    
    Returns:
        Dictionary mapping table_id to output file path
    
    Warning:
        - Higher concurrency may trigger rate limits
        - Recommended max_workers: 5-10
        - Monitor for 429 (Too Many Requests) errors
    
    Example:
        results = batch_export_tables_parallel(
            table_ids=['in.c-main.table1', 'in.c-main.table2'],
            max_workers=5
        )
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    failed = {}
    
    print(f"Starting parallel export of {len(table_ids)} tables (workers: {max_workers})...")
    
    def export_one_table(table_id):
        """Export single table (thread worker function)."""
        output_file = os.path.join(
            output_dir,
            f"{table_id.replace('.', '_')}.csv"
        )
        export_table_with_retry(table_id, output_file, **export_params)
        return table_id, output_file
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(export_one_table, tid): tid for tid in table_ids}
        
        for future in as_completed(futures):
            table_id = futures[future]
            try:
                tid, output_file = future.result()
                results[tid] = output_file
                print(f"✓ Completed: {tid}")
            except Exception as e:
                failed[table_id] = str(e)
                print(f"✗ Failed: {table_id} - {e}")
    
    print(f"\n=== Batch Export Complete ===")
    print(f"Success: {len(results)}/{len(table_ids)} tables")
    if failed:
        print(f"Failed: {len(failed)} tables")
    
    if failed:
        raise Exception(f"Batch export completed with {len(failed)} failures")
    
    return results
```

#### Filtered Export

Export multiple tables with SQL filtering:

```python
def batch_export_with_filter(
    table_configs: List[Dict[str, Any]],
    output_dir: str = "exports"
) -> Dict[str, str]:
    """
    Export tables with individual filter configurations.
    
    Args:
        table_configs: List of table configurations with filters
        output_dir: Output directory
    
    Table config structure:
        {
            'table_id': 'in.c-main.customers',
            'whereColumn': 'status',        # Column to filter on
            'whereValues': ['active'],      # Values to match
            'whereOperator': 'eq',          # Operator: eq, ne, gt, lt, ge, le
            'changedSince': '2024-01-01'   # Optional: incremental export
        }
    
    Available whereOperator values:
        - 'eq': Equal (column = value)
        - 'ne': Not equal (column != value)
        - 'gt': Greater than (column > value)
        - 'lt': Less than (column < value)
        - 'ge': Greater than or equal (column >= value)
        - 'le': Less than or equal (column <= value)
    
    Example:
        configs = [
            {
                'table_id': 'in.c-main.customers',
                'whereColumn': 'status',
                'whereValues': ['active', 'pending'],
                'whereOperator': 'eq'
            },
            {
                'table_id': 'in.c-main.orders',
                'whereColumn': 'order_date',
                'whereValues': ['2024-01-01'],
                'whereOperator': 'ge',
                'changedSince': '2024-01-01T00:00:00Z'
            }
        ]
        results = batch_export_with_filter(configs)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for config in table_configs:
        table_id = config['table_id']
        print(f"\nExporting {table_id} with filters...")
        
        # Build export parameters
        export_params = {}
        if 'whereColumn' in config:
            export_params['whereColumn'] = config['whereColumn']
        if 'whereValues' in config:
            export_params['whereValues'] = config['whereValues']
        if 'whereOperator' in config:
            export_params['whereOperator'] = config['whereOperator']
        if 'changedSince' in config:
            export_params['changedSince'] = config['changedSince']
        
        output_file = os.path.join(
            output_dir,
            f"{table_id.replace('.', '_')}_filtered.csv"
        )
        
        results[table_id] = export_table_with_retry(
            table_id,
            output_file,
            **export_params
        )
    
    return results
```

### Batch Import

Import multiple CSV files into Keboola tables.

#### Sequential Import

```python
def batch_import_tables(
    import_configs: List[Dict[str, Any]],
    incremental: bool = False
) -> Dict[str, str]:
    """
    Import multiple CSV files to Keboola tables.
    
    Args:
        import_configs: List of import configurations
        incremental: If True, use incremental mode for all imports
    
    Import config structure:
        {
            'table_id': 'in.c-main.customers',  # Target table
            'file_path': 'data/customers.csv',  # Source CSV file
            'incremental': True,                 # Optional: override global setting
            'primary_key': ['id']               # Required for incremental
        }
    
    Returns:
        Dictionary mapping table_id to job_id
    
    Example:
        configs = [
            {
                'table_id': 'in.c-main.customers',
                'file_path': 'exports/customers.csv',
                'incremental': True,
                'primary_key': ['id']
            },
            {
                'table_id': 'in.c-main.orders',
                'file_path': 'exports/orders.csv'
            }
        ]
        results = batch_import_tables(configs)
    """
    results = {}
    failed = {}
    
    print(f"Starting batch import of {len(import_configs)} tables...")
    
    for i, config in enumerate(import_configs, 1):
        table_id = config['table_id']
        file_path = config['file_path']
        is_incremental = config.get('incremental', incremental)
        
        print(f"\n[{i}/{len(import_configs)}] Importing {table_id}")
        
        try:
            # Verify file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read CSV data
            with open(file_path, 'rb') as f:
                csv_data = f.read()
            
            # Set primary key if incremental and specified
            if is_incremental and 'primary_key' in config:
                print(f"Setting primary key: {config['primary_key']}")
                pk_response = requests.post(
                    f"https://{stack_url}/v2/storage/tables/{table_id}",
                    headers={"X-StorageApi-Token": token},
                    json={"primaryKey": config['primary_key']}
                )
                pk_response.raise_for_status()
            
            # Start import job
            params = {}
            if is_incremental:
                params['incremental'] = '1'
            
            response = requests.post(
                f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
                headers={
                    "X-StorageApi-Token": token,
                    "Content-Type": "text/csv"
                },
                params=params,
                data=csv_data
            )
            response.raise_for_status()
            job_id = response.json()["id"]
            
            # Poll for completion using helper
            poll_job_until_complete(job_id, timeout=600, poll_interval=3)
            
            results[table_id] = job_id
            print(f"✓ Imported {table_id}")
            
        except Exception as e:
            print(f"✗ Failed to import {table_id}: {e}")
            failed[table_id] = str(e)
    
    print(f"\n=== Batch Import Complete ===")
    print(f"Success: {len(results)}/{len(import_configs)} tables")
    if failed:
        print(f"Failed: {len(failed)} tables")
        for table_id, error in failed.items():
            print(f"  - {table_id}: {error}")
    
    if failed:
        raise Exception(f"Batch import completed with {len(failed)} failures")
    
    return results
```

### Performance Considerations

#### Choosing Export Strategy

**Use Sequential Export when**:
- Exporting many tables (>20)
- Tables are very large (>1GB each)
- Rate limiting is a concern
- You need predictable resource usage

**Use Parallel Export when**:
- Exporting few tables (<20)
- Tables are small to medium (<500MB each)
- Speed is critical
- You have verified rate limits allow concurrency

#### Optimization Tips

```python
# 1. Use filtered exports to reduce data transfer
export_params = {
    'whereColumn': 'date',
    'whereValues': ['2024-01-01'],
    'whereOperator': 'ge'  # Only export rows where date >= 2024-01-01
}

# 2. Use incremental exports for changed data only
export_params = {
    'changedSince': '2024-01-01T00:00:00Z'  # Only export modified rows
}

# 3. Adjust parallel workers based on table sizes
if avg_table_size_mb < 100:
    max_workers = 10  # Small tables: more concurrency
elif avg_table_size_mb < 500:
    max_workers = 5   # Medium tables: moderate concurrency
else:
    max_workers = 2   # Large tables: minimal concurrency

# 4. Monitor and handle rate limits
try:
    results = batch_export_tables_parallel(table_ids, max_workers=5)
except Exception as e:
    if '429' in str(e):  # Rate limited
        print("Rate limit hit, retrying with sequential export...")
        results = batch_export_tables_sequential(table_ids)
    else:
        raise
```

#### Memory Management

```python
# For very large imports, stream data instead of loading into memory
def import_large_file(table_id: str, file_path: str):
    """
    Import large file using streaming upload.
    """
    # Upload file to Keboola Files first
    with open(file_path, 'rb') as f:
        upload_response = requests.post(
            f"https://{stack_url}/v2/storage/files",
            headers={"X-StorageApi-Token": token},
            files={'file': f}
        )
    upload_response.raise_for_status()
    file_id = upload_response.json()['id']
    
    # Import from uploaded file
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={"X-StorageApi-Token": token},
        json={'dataFileId': file_id}
    )
    response.raise_for_status()
    
    return poll_job_until_complete(response.json()['id'])
```

#### Complete Example

```python
# Initialize variables (see Prerequisites section)
import os
import requests
from typing import List, Dict, Any

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

# Define tables to process
table_ids = [
    'in.c-main.customers',
    'in.c-main.orders',
    'in.c-main.products'
]

# Step 1: Export all tables with filter
print("Step 1: Exporting tables...")
export_results = batch_export_tables_sequential(
    table_ids,
    output_dir='exports',
    changedSince='2024-01-01T00:00:00Z'  # Only export recent data
)

# Step 2: Process exported files (example: data transformation)
print("\nStep 2: Processing data...")
import pandas as pd

for table_id, file_path in export_results.items():
    df = pd.read_csv(file_path)
    # Perform transformations
    df['processed_date'] = pd.Timestamp.now()
    # Save processed file
    df.to_csv(file_path, index=False)
    print(f"Processed {table_id}: {len(df)} rows")

# Step 3: Import processed files back
print("\nStep 3: Importing processed data...")
import_configs = [
    {
        'table_id': table_id,
        'file_path': file_path,
        'incremental': True,
        'primary_key': ['id']
    }
    for table_id, file_path in export_results.items()
]

import_results = batch_import_tables(import_configs)

print("\n=== Pipeline Complete ===")
print(f"Exported: {len(export_results)} tables")
print(f"Imported: {len(import_results)} tables")
```
