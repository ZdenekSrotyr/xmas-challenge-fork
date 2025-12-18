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

### Exporting Multiple Tables

Keboola Storage API doesn't have a single "batch export" endpoint, but you can efficiently export multiple tables using concurrent async jobs:

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def start_table_export(table_id):
    """Start async export job for a table."""
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    return {
        "table_id": table_id,
        "job_id": response.json()["id"]
    }

def wait_for_export_job(job_info, timeout=300):
    """Wait for export job and download result."""
    job_id = job_info["job_id"]
    table_id = job_info["table_id"]
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        response.raise_for_status()
        job = response.json()
        
        if job["status"] == "success":
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            # Save to file with sanitized table name
            filename = f"{table_id.replace('.', '_')}.csv"
            with open(filename, "wb") as f:
                f.write(data_response.content)
            
            return {
                "table_id": table_id,
                "filename": filename,
                "status": "success"
            }
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            return {
                "table_id": table_id,
                "status": "failed",
                "error": error_msg
            }
        
        time.sleep(2)
    
    return {
        "table_id": table_id,
        "status": "timeout",
        "error": f"Export did not complete within {timeout}s"
    }

def export_tables_batch(table_ids, max_workers=5):
    """Export multiple tables concurrently.
    
    Args:
        table_ids: List of table IDs to export
        max_workers: Maximum concurrent export jobs (default: 5)
    
    Returns:
        List of result dictionaries with status for each table
    """
    print(f"Starting batch export of {len(table_ids)} tables...")
    
    # Start all export jobs
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all export job starts
        start_futures = {
            executor.submit(start_table_export, table_id): table_id 
            for table_id in table_ids
        }
        
        job_infos = []
        for future in as_completed(start_futures):
            try:
                job_info = future.result()
                job_infos.append(job_info)
                print(f"Started export job {job_info['job_id']} for {job_info['table_id']}")
            except Exception as e:
                table_id = start_futures[future]
                print(f"Failed to start export for {table_id}: {e}")
                job_infos.append({
                    "table_id": table_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Wait for all jobs to complete
        wait_futures = {
            executor.submit(wait_for_export_job, job_info): job_info["table_id"]
            for job_info in job_infos if "job_id" in job_info
        }
        
        results = []
        for future in as_completed(wait_futures):
            try:
                result = future.result()
                results.append(result)
                if result["status"] == "success":
                    print(f"✓ Exported {result['table_id']} to {result['filename']}")
                else:
                    print(f"✗ Failed {result['table_id']}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                table_id = wait_futures[future]
                print(f"✗ Exception for {table_id}: {e}")
                results.append({
                    "table_id": table_id,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nBatch export complete: {success_count}/{len(table_ids)} successful")
    
    return results

# Usage example
table_ids = [
    "in.c-main.customers",
    "in.c-main.orders",
    "in.c-main.products",
    "in.c-sales.transactions"
]

results = export_tables_batch(table_ids, max_workers=5)

# Check for failures
failed = [r for r in results if r["status"] != "success"]
if failed:
    print("\nFailed exports:")
    for result in failed:
        print(f"  {result['table_id']}: {result.get('error', 'Unknown')}")
```

### Batch Import Pattern

Import multiple CSV files to different tables:

```python
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed

def import_table_file(table_id, csv_file):
    """Import CSV file to existing table.
    
    Args:
        table_id: Target table ID (e.g., 'in.c-main.customers')
        csv_file: Path to CSV file
    
    Returns:
        Dict with import status
    """
    try:
        # Read CSV data
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        
        # Start async import
        response = requests.post(
            f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
            headers={
                "X-StorageApi-Token": token,
                "Content-Type": "text/csv"
            },
            params={"dataString": csv_data}
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
                return {
                    "table_id": table_id,
                    "file": csv_file,
                    "status": "success",
                    "rows_imported": job.get("results", {}).get("importedRowsCount", 0)
                }
            
            elif job["status"] in ["error", "cancelled", "terminated"]:
                error_msg = job.get("error", {}).get("message", "Unknown error")
                return {
                    "table_id": table_id,
                    "file": csv_file,
                    "status": "failed",
                    "error": error_msg
                }
            
            time.sleep(2)
        
        return {
            "table_id": table_id,
            "file": csv_file,
            "status": "timeout",
            "error": "Import did not complete within timeout"
        }
    
    except Exception as e:
        return {
            "table_id": table_id,
            "file": csv_file,
            "status": "failed",
            "error": str(e)
        }

def batch_import_directory(import_mapping, max_workers=3):
    """Import multiple CSV files to their respective tables.
    
    Args:
        import_mapping: Dict mapping table IDs to CSV file paths
            e.g., {"in.c-main.customers": "customers.csv"}
        max_workers: Maximum concurrent imports (default: 3)
    
    Returns:
        List of import results
    """
    print(f"Starting batch import of {len(import_mapping)} tables...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(import_table_file, table_id, csv_file): table_id
            for table_id, csv_file in import_mapping.items()
        }
        
        results = []
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result["status"] == "success":
                print(f"✓ Imported {result['rows_imported']} rows to {result['table_id']}")
            else:
                print(f"✗ Failed {result['table_id']}: {result.get('error', 'Unknown')}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nBatch import complete: {success_count}/{len(import_mapping)} successful")
    
    return results

# Usage example
import_mapping = {
    "in.c-main.customers": "data/customers.csv",
    "in.c-main.orders": "data/orders.csv",
    "in.c-main.products": "data/products.csv"
}

results = batch_import_directory(import_mapping, max_workers=3)
```

### Batch Operations for an Entire Bucket

Export or import all tables in a bucket:

```python
def get_bucket_tables(bucket_id):
    """Get list of all tables in a bucket."""
    response = requests.get(
        f"https://{stack_url}/v2/storage/buckets/{bucket_id}/tables",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    return [table["id"] for table in response.json()]

def export_entire_bucket(bucket_id, output_dir="./exports", max_workers=5):
    """Export all tables from a bucket.
    
    Args:
        bucket_id: Bucket ID (e.g., 'in.c-main')
        output_dir: Directory to save exported files
        max_workers: Maximum concurrent exports
    
    Returns:
        List of export results
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all tables in bucket
    table_ids = get_bucket_tables(bucket_id)
    print(f"Found {len(table_ids)} tables in bucket {bucket_id}")
    
    # Export all tables
    return export_tables_batch(table_ids, max_workers=max_workers)

# Usage
results = export_entire_bucket("in.c-main", output_dir="./bucket_exports")
```

### Performance Considerations

**Concurrency Limits**:
- **Recommended**: 3-5 concurrent operations for imports, 5-10 for exports
- **API Rate Limits**: ~30 requests/minute per token
- **Job Slots**: Projects have limited concurrent job slots (typically 5-10)

**Best Practices**:

```python
# ✓ GOOD: Limit concurrency to avoid overwhelming the API
export_tables_batch(table_ids, max_workers=5)

# ✗ BAD: Too many concurrent requests
export_tables_batch(table_ids, max_workers=50)  # Will hit rate limits

# ✓ GOOD: Use smaller batches for large operations
def export_in_batches(table_ids, batch_size=10, max_workers=5):
    """Export tables in smaller batches."""
    results = []
    for i in range(0, len(table_ids), batch_size):
        batch = table_ids[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(table_ids) + batch_size - 1)//batch_size}")
        batch_results = export_tables_batch(batch, max_workers=max_workers)
        results.extend(batch_results)
        time.sleep(5)  # Pause between batches
    return results

# Usage for large bucket
table_ids = get_bucket_tables("in.c-main")
if len(table_ids) > 20:
    results = export_in_batches(table_ids, batch_size=10, max_workers=5)
else:
    results = export_tables_batch(table_ids, max_workers=5)
```

**Memory Management**:

```python
# ✓ GOOD: Stream large files to disk
def download_export_streaming(file_url, output_path):
    """Download large export file with streaming."""
    response = requests.get(file_url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# ✗ BAD: Load entire file into memory
data_response = requests.get(file_url)
content = data_response.content  # Entire file in memory
```

**Error Handling**:

```python
def robust_batch_export(table_ids, max_retries=2):
    """Batch export with automatic retry for failures."""
    results = export_tables_batch(table_ids)
    
    # Retry failed exports
    for retry in range(max_retries):
        failed_tables = [
            r["table_id"] for r in results 
            if r["status"] != "success"
        ]
        
        if not failed_tables:
            break
        
        print(f"\nRetry {retry + 1}/{max_retries} for {len(failed_tables)} failed tables")
        time.sleep(10)  # Wait before retry
        
        retry_results = export_tables_batch(failed_tables)
        
        # Update results
        for retry_result in retry_results:
            for i, r in enumerate(results):
                if r["table_id"] == retry_result["table_id"]:
                    results[i] = retry_result
                    break
    
    return results
```

**Monitoring Progress**:

```python
import json
from datetime import datetime

def export_with_logging(table_ids, log_file="export_log.json"):
    """Export tables with detailed logging."""
    start_time = datetime.now()
    
    results = export_tables_batch(table_ids)
    
    # Create detailed log
    log_data = {
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat(),
        "total_tables": len(table_ids),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] != "success"),
        "results": results
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\nLog saved to {log_file}")
    return results
```
