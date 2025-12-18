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
# Upload CSV file to create a NEW table
csv_data = "id,name,value\n1,foo,100\n2,bar,200"

response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={
        "X-StorageApi-Token": token
    },
    params={
        "name": "my_table",
        "primaryKey": "id"  # Optional: set primary key
    },
    data=csv_data
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll job until completion
timeout = 300
start_time = time.time()

while time.time() - start_time < timeout:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()
    job = job_response.json()
    
    if job["status"] == "success":
        table_id = job["results"]["id"]
        print(f"Table created: {table_id}")
        break
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Job failed: {error_msg}")
    
    time.sleep(2)
else:
    raise TimeoutError(f"Job did not complete within {timeout}s")
```

**Note**: If the table already exists, this operation will fail. Use the import endpoint instead to add data to existing tables.

### Import Data to Existing Table

```python
# Import data to an EXISTING table
table_id = "in.c-main.my_table"
csv_data = "id,name,value\n3,baz,300\n4,qux,400"

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": token},
    data=csv_data
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll job until completion
timeout = 300
start_time = time.time()

while time.time() - start_time < timeout:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()
    job = job_response.json()
    
    if job["status"] == "success":
        print(f"Data imported successfully")
        break
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Import failed: {error_msg}")
    
    time.sleep(2)
else:
    raise TimeoutError(f"Import did not complete within {timeout}s")
```

### Incremental Loads (Append/Update Data)

**Important**: Incremental loads require the table to have a primary key defined.

```python
# Incremental load: append new rows or update existing rows by primary key
table_id = "in.c-main.my_table"
csv_data = "id,name,value\n1,foo_updated,150\n5,new_row,500"

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": token},
    params={"incremental": "1"},
    data=csv_data
)
response.raise_for_status()

job_id = response.json()["id"]

# Poll job until completion
timeout = 300
start_time = time.time()

while time.time() - start_time < timeout:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()
    job = job_response.json()
    
    if job["status"] == "success":
        print(f"Incremental load completed")
        break
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Incremental load failed: {error_msg}")
    
    time.sleep(2)
else:
    raise TimeoutError(f"Job did not complete within {timeout}s")
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

Use `changedSince` parameter to export only rows modified after a specific timestamp. This filters based on the row's internal modification timestamp maintained by Keboola Storage.

**When to use**: 
- Incremental data synchronization
- Change data capture patterns
- Reducing data transfer for large tables

**Important**: `changedSince` filters by row modification time (when the row was last updated in Storage), not by values in your data columns. If you need to filter by a date column in your data, use a different approach.

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

# Poll for completion
timeout = 300
start_time = time.time()

while time.time() - start_time < timeout:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )
    job_response.raise_for_status()
    job = job_response.json()
    
    if job["status"] == "success":
        file_url = job["results"]["file"]["url"]
        data_response = requests.get(file_url)
        with open("changed_data.csv", "wb") as f:
            f.write(data_response.content)
        print(f"Exported {len(data_response.content)} bytes of changed data")
        break
    elif job["status"] in ["error", "cancelled", "terminated"]:
        error_msg = job.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Export failed: {error_msg}")
    
    time.sleep(2)
else:
    raise TimeoutError(f"Export did not complete within {timeout}s")
```

**Alternative: Filter by data column**

If you need to filter by a date column in your data (not modification time), export the full table and filter locally, or use a transformation:

```python
# If you need to filter by a date column in your data
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token},
    params={
        "whereColumn": "created_date",
        "whereValues": ["2024-01-01"],
        "whereOperator": "ge"  # greater than or equal
    }
)
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

### Overview

Batch operations allow you to process multiple tables efficiently in a single workflow. Common use cases:
- Exporting multiple related tables for analysis
- Importing data to multiple tables in parallel
- Bulk table management operations

### Batch Table Export

Export multiple tables concurrently to improve performance:

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def export_table(table_id, output_dir="."):
    """Export a single table and return the file path."""
    # Start async export
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # Poll for completion
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
            # Download file
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            # Save to file
            filename = f"{output_dir}/{table_id.replace('.', '_')}.csv"
            with open(filename, "wb") as f:
                f.write(data_response.content)
            
            return {"table_id": table_id, "file": filename, "status": "success"}
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            return {"table_id": table_id, "status": "failed", "error": error_msg}
        
        time.sleep(2)
    
    return {"table_id": table_id, "status": "timeout"}

def batch_export_tables(table_ids, output_dir=".", max_parallel=3):
    """Export multiple tables in parallel.
    
    Args:
        table_ids: List of table IDs to export
        output_dir: Directory to save exported files
        max_parallel: Maximum concurrent exports (default 3)
    
    Returns:
        List of results with status for each table
    """
    results = []
    
    # Use ThreadPoolExecutor for concurrent exports
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        # Submit all export jobs
        future_to_table = {
            executor.submit(export_table, table_id, output_dir): table_id
            for table_id in table_ids
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_table):
            table_id = future_to_table[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed: {table_id} - {result['status']}")
            except Exception as e:
                results.append({
                    "table_id": table_id,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"Failed: {table_id} - {e}")
    
    return results

# Usage example
tables_to_export = [
    "in.c-main.customers",
    "in.c-main.orders",
    "in.c-main.products"
]

results = batch_export_tables(tables_to_export, output_dir="./exports", max_parallel=3)

# Print summary
successful = sum(1 for r in results if r["status"] == "success")
failed = sum(1 for r in results if r["status"] == "failed")
print(f"\nExport completed: {successful} successful, {failed} failed")
```

### Batch Table Import

Import data to multiple tables in parallel:

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def import_table(table_id, csv_file_path, incremental=False):
    """Import CSV data to a table.
    
    Args:
        table_id: Target table ID
        csv_file_path: Path to CSV file
        incremental: Whether to use incremental load
    
    Returns:
        Dictionary with import result
    """
    # Read CSV data
    with open(csv_file_path, "r", encoding="utf-8") as f:
        csv_data = f.read()
    
    # Start async import
    params = {}
    if incremental:
        params["incremental"] = "1"
    
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={"X-StorageApi-Token": token},
        params=params,
        data=csv_data
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # Poll for completion
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
            return {
                "table_id": table_id,
                "file": csv_file_path,
                "status": "success"
            }
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            return {
                "table_id": table_id,
                "file": csv_file_path,
                "status": "failed",
                "error": error_msg
            }
        
        time.sleep(2)
    
    return {
        "table_id": table_id,
        "file": csv_file_path,
        "status": "timeout"
    }

def batch_import_tables(import_mappings, incremental=False, max_parallel=3):
    """Import data to multiple tables in parallel.
    
    Args:
        import_mappings: List of {"table_id": "...", "file": "..."} dicts
        incremental: Whether to use incremental load
        max_parallel: Maximum concurrent imports
    
    Returns:
        List of results with status for each import
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        # Submit all import jobs
        future_to_mapping = {
            executor.submit(
                import_table,
                mapping["table_id"],
                mapping["file"],
                incremental
            ): mapping
            for mapping in import_mappings
        }
        
        # Collect results
        for future in as_completed(future_to_mapping):
            mapping = future_to_mapping[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed: {mapping['table_id']} - {result['status']}")
            except Exception as e:
                results.append({
                    "table_id": mapping["table_id"],
                    "file": mapping["file"],
                    "status": "failed",
                    "error": str(e)
                })
                print(f"Failed: {mapping['table_id']} - {e}")
    
    return results

# Usage example
import_mappings = [
    {"table_id": "in.c-main.customers", "file": "./data/customers.csv"},
    {"table_id": "in.c-main.orders", "file": "./data/orders.csv"},
    {"table_id": "in.c-main.products", "file": "./data/products.csv"}
]

results = batch_import_tables(import_mappings, incremental=True, max_parallel=3)

# Print summary
successful = sum(1 for r in results if r["status"] == "success")
failed = sum(1 for r in results if r["status"] == "failed")
print(f"\nImport completed: {successful} successful, {failed} failed")
```

### Performance Considerations

**Parallel Processing**:
- Default `max_parallel=3` is safe for most use cases
- Increase for larger projects with higher rate limits
- Decrease if hitting rate limits (429 errors)
- Monitor job completion times to optimize

**Rate Limits**:
- Keboola enforces rate limits per token (~30 requests/minute)
- Batch operations distribute requests over time
- Use exponential backoff for 429 errors
- Consider separate tokens for different workflows

**Memory Usage**:
- Batch exports stream to disk, not memory
- Each concurrent operation uses one thread
- Safe to export hundreds of tables with proper threading

**Error Handling**:
- Individual table failures don't stop batch operation
- Collect all results before reporting
- Retry failed operations separately
- Log errors for debugging

**Benchmarks** (varies by table size and complexity):
- Single table export: 5-30 seconds
- 10 tables sequential: 50-300 seconds
- 10 tables parallel (max_parallel=3): 20-120 seconds
- Network and backend processing are main bottlenecks

**Example: Optimizing max_workers**

```python
import os

# Adjust based on project size and rate limits
PROJECT_SIZE = os.environ.get("KEBOOLA_PROJECT_SIZE", "medium")

MAX_WORKERS_CONFIG = {
    "small": 2,   # <100 tables, conservative
    "medium": 3,  # 100-500 tables, balanced
    "large": 5    # >500 tables, aggressive
}

max_workers = MAX_WORKERS_CONFIG.get(PROJECT_SIZE, 3)

results = batch_export_tables(
    table_ids,
    max_parallel=max_workers
)
```

### Troubleshooting Batch Operations

**Issue: Too many 429 (Rate Limit) errors**

```python
# Solution: Reduce max_parallel and add retry logic
import time
from requests.exceptions import HTTPError

def export_table_with_retry(table_id, max_retries=3):
    """Export with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            return export_table(table_id)
        except HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
    return {"table_id": table_id, "status": "failed", "error": "Max retries exceeded"}

# Use lower max_parallel
results = batch_export_tables(table_ids, max_parallel=2)
```

**Issue: Some tables timeout**

```python
# Solution: Increase timeout for large tables
def export_large_table(table_id, timeout=1800):  # 30 minutes
    # Modify timeout in export_table function
    # ... (same logic with longer timeout)
    pass
```

**Issue: Memory errors with many concurrent operations**

```python
# Solution: Process in smaller batches
def batch_export_in_chunks(table_ids, chunk_size=10, max_parallel=3):
    """Export tables in chunks to limit memory usage."""
    all_results = []
    
    for i in range(0, len(table_ids), chunk_size):
        chunk = table_ids[i:i + chunk_size]
        print(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} tables")
        results = batch_export_tables(chunk, max_parallel=max_parallel)
        all_results.extend(results)
        time.sleep(5)  # Brief pause between chunks
    
    return all_results
```
