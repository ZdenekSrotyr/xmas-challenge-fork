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

### Batch Export Multiple Tables

Export multiple tables concurrently using async jobs:

```python
import requests
import time
import concurrent.futures
from typing import List, Dict

def start_table_export(table_id: str, stack_url: str, token: str) -> Dict:
    """Start async export job for a single table."""
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    
    job = response.json()
    return {
        "table_id": table_id,
        "job_id": job["id"],
        "status": "started"
    }

def wait_for_export_job(job_id: str, stack_url: str, token: str, timeout: int = 300) -> Dict:
    """Poll export job until completion."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
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
            raise Exception(f"Job {job_id} failed: {error_msg}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Job {job_id} timeout after {timeout}s")

def download_export_file(job: Dict, output_path: str) -> str:
    """Download exported file from completed job."""
    file_url = job["results"]["file"]["url"]
    response = requests.get(file_url)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

def batch_export_tables(table_ids: List[str], stack_url: str, token: str, output_dir: str = "exports") -> Dict[str, str]:
    """Export multiple tables in parallel.
    
    Args:
        table_ids: List of table IDs to export (e.g., ['in.c-main.customers', 'in.c-main.orders'])
        stack_url: Keboola stack URL
        token: Storage API token
        output_dir: Directory to save exported files
    
    Returns:
        Dictionary mapping table_id to output file path
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Start all export jobs
    print(f"Starting export jobs for {len(table_ids)} tables...")
    jobs = []
    for table_id in table_ids:
        try:
            job = start_table_export(table_id, stack_url, token)
            jobs.append(job)
            print(f"  Started: {table_id} (job {job['job_id']})")
        except Exception as e:
            print(f"  Failed to start {table_id}: {e}")
    
    # Step 2: Wait for all jobs to complete
    print(f"\nWaiting for {len(jobs)} jobs to complete...")
    completed_jobs = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_job = {
            executor.submit(wait_for_export_job, job["job_id"], stack_url, token): job
            for job in jobs
        }
        
        for future in concurrent.futures.as_completed(future_to_job):
            job_info = future_to_job[future]
            try:
                completed_job = future.result()
                completed_jobs.append({
                    "table_id": job_info["table_id"],
                    "job": completed_job
                })
                print(f"  Completed: {job_info['table_id']}")
            except Exception as e:
                print(f"  Failed: {job_info['table_id']} - {e}")
    
    # Step 3: Download all files
    print(f"\nDownloading {len(completed_jobs)} files...")
    results = {}
    
    for item in completed_jobs:
        table_id = item["table_id"]
        job = item["job"]
        
        # Generate safe filename from table ID
        filename = table_id.replace(".", "_") + ".csv"
        output_path = os.path.join(output_dir, filename)
        
        try:
            download_export_file(job, output_path)
            results[table_id] = output_path
            print(f"  Downloaded: {table_id} -> {output_path}")
        except Exception as e:
            print(f"  Download failed: {table_id} - {e}")
    
    return results

# Usage example
table_ids = [
    "in.c-main.customers",
    "in.c-main.orders",
    "in.c-main.products",
    "in.c-sales.transactions"
]

stack_url = os.environ["KEBOOLA_STACK_URL"]
token = os.environ["KEBOOLA_TOKEN"]

results = batch_export_tables(table_ids, stack_url, token, output_dir="./data")

print(f"\nExport complete. Downloaded {len(results)} tables:")
for table_id, path in results.items():
    print(f"  {table_id}: {path}")
```

### Batch Import Multiple Tables

Import multiple CSV files to different tables:

```python
import os
import glob
from typing import List, Dict

def start_table_import(table_id: str, csv_path: str, stack_url: str, token: str, incremental: bool = False) -> Dict:
    """Start async import job for a single table."""
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_data = f.read()
    
    params = {"dataString": csv_data}
    if incremental:
        params["incremental"] = "1"
    
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={
            "X-StorageApi-Token": token,
            "Content-Type": "text/csv"
        },
        params=params
    )
    response.raise_for_status()
    
    job = response.json()
    return {
        "table_id": table_id,
        "csv_path": csv_path,
        "job_id": job["id"],
        "status": "started"
    }

def wait_for_import_job(job_id: str, stack_url: str, token: str, timeout: int = 300) -> Dict:
    """Poll import job until completion."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
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
            raise Exception(f"Job {job_id} failed: {error_msg}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Job {job_id} timeout after {timeout}s")

def batch_import_tables(imports: List[Dict[str, str]], stack_url: str, token: str, incremental: bool = False) -> Dict[str, bool]:
    """Import multiple CSV files to tables in parallel.
    
    Args:
        imports: List of dicts with 'table_id' and 'csv_path' keys
                 Example: [{'table_id': 'in.c-main.customers', 'csv_path': './customers.csv'}]
        stack_url: Keboola stack URL
        token: Storage API token
        incremental: If True, perform incremental loads (requires primary keys)
    
    Returns:
        Dictionary mapping table_id to success status (True/False)
    """
    # Step 1: Start all import jobs
    print(f"Starting import jobs for {len(imports)} tables...")
    jobs = []
    
    for item in imports:
        table_id = item["table_id"]
        csv_path = item["csv_path"]
        
        try:
            job = start_table_import(table_id, csv_path, stack_url, token, incremental)
            jobs.append(job)
            print(f"  Started: {table_id} from {csv_path} (job {job['job_id']})")
        except Exception as e:
            print(f"  Failed to start {table_id}: {e}")
    
    # Step 2: Wait for all jobs to complete
    print(f"\nWaiting for {len(jobs)} import jobs to complete...")
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_job = {
            executor.submit(wait_for_import_job, job["job_id"], stack_url, token): job
            for job in jobs
        }
        
        for future in concurrent.futures.as_completed(future_to_job):
            job_info = future_to_job[future]
            table_id = job_info["table_id"]
            
            try:
                completed_job = future.result()
                results[table_id] = True
                print(f"  Completed: {table_id}")
            except Exception as e:
                results[table_id] = False
                print(f"  Failed: {table_id} - {e}")
    
    return results

# Usage example 1: Import from directory
imports = [
    {"table_id": "in.c-main.customers", "csv_path": "./data/customers.csv"},
    {"table_id": "in.c-main.orders", "csv_path": "./data/orders.csv"},
    {"table_id": "in.c-main.products", "csv_path": "./data/products.csv"}
]

stack_url = os.environ["KEBOOLA_STACK_URL"]
token = os.environ["KEBOOLA_TOKEN"]

results = batch_import_tables(imports, stack_url, token, incremental=False)

print(f"\nImport complete: {sum(results.values())}/{len(results)} succeeded")

# Usage example 2: Auto-discover CSV files in directory
def batch_import_from_directory(csv_dir: str, bucket_id: str, stack_url: str, token: str) -> Dict[str, bool]:
    """Import all CSV files from directory to specified bucket.
    
    File names become table names (e.g., customers.csv -> in.c-main.customers)
    """
    imports = []
    
    for csv_path in glob.glob(os.path.join(csv_dir, "*.csv")):
        filename = os.path.basename(csv_path)
        table_name = os.path.splitext(filename)[0]  # Remove .csv extension
        table_id = f"{bucket_id}.{table_name}"
        
        imports.append({
            "table_id": table_id,
            "csv_path": csv_path
        })
    
    return batch_import_tables(imports, stack_url, token)

# Usage
results = batch_import_from_directory(
    csv_dir="./exports",
    bucket_id="in.c-main",
    stack_url=stack_url,
    token=token
)
```

### Performance Considerations

#### Concurrent Job Limits

Keboola has per-project concurrency limits for async jobs:

- **Default limit**: 10 concurrent jobs per project
- **Recommended batch size**: 5-10 tables per batch
- **Rate limiting**: Jobs are queued if limit exceeded

```python
def batch_export_with_limit(table_ids: List[str], stack_url: str, token: str, max_concurrent: int = 5):
    """Export tables in batches to respect concurrency limits."""
    results = {}
    
    # Process in batches
    for i in range(0, len(table_ids), max_concurrent):
        batch = table_ids[i:i + max_concurrent]
        print(f"\nProcessing batch {i//max_concurrent + 1}: {len(batch)} tables")
        
        batch_results = batch_export_tables(batch, stack_url, token)
        results.update(batch_results)
        
        # Optional: Add delay between batches
        if i + max_concurrent < len(table_ids):
            time.sleep(5)
    
    return results
```

#### Optimization Tips

**1. Filter data at export time**:
```python
# Export only recent data
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token},
    params={
        "changedSince": yesterday,  # Only rows modified since timestamp
        "limit": 10000  # Limit number of rows
    }
)
```

**2. Use incremental imports**:
```python
# Faster imports when only adding/updating rows
results = batch_import_tables(
    imports,
    stack_url,
    token,
    incremental=True  # Only updates changed rows
)
```

**3. Monitor job progress**:
```python
def monitor_batch_progress(job_ids: List[str], stack_url: str, token: str):
    """Monitor progress of multiple jobs."""
    while job_ids:
        time.sleep(5)
        
        for job_id in list(job_ids):
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token}
            )
            job = response.json()
            
            if job["status"] in ["success", "error", "cancelled"]:
                print(f"Job {job_id}: {job['status']}")
                job_ids.remove(job_id)
        
        if job_ids:
            print(f"Waiting for {len(job_ids)} jobs...")
```

**4. Handle large files**:
```python
# For files > 100MB, use file upload API instead of dataString parameter
def import_large_file(table_id: str, csv_path: str, stack_url: str, token: str):
    """Import large CSV file via file upload."""
    # Step 1: Upload file
    with open(csv_path, "rb") as f:
        upload_response = requests.post(
            f"https://{stack_url}/v2/storage/files",
            headers={"X-StorageApi-Token": token},
            files={"file": f}
        )
    upload_response.raise_for_status()
    file_id = upload_response.json()["id"]
    
    # Step 2: Import from uploaded file
    import_response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={"X-StorageApi-Token": token},
        json={"dataFileId": file_id}
    )
    import_response.raise_for_status()
    
    return import_response.json()["id"]
```

#### Performance Benchmarks

**Typical export times** (on US stack):
- Small table (< 10K rows): 5-10 seconds
- Medium table (100K-1M rows): 30-60 seconds
- Large table (> 1M rows): 2-5 minutes

**Typical import times**:
- Small file (< 1MB): 5-10 seconds
- Medium file (10-100MB): 30-90 seconds
- Large file (> 100MB): 2-10 minutes

**Batch operation overhead**:
- Starting 10 jobs: ~2-5 seconds
- Polling overhead: ~1-2 seconds per job
- Total batch (10 small tables): ~30-60 seconds

### Error Handling in Batch Operations

```python
def batch_export_with_retry(table_ids: List[str], stack_url: str, token: str, max_retries: int = 3):
    """Export tables with automatic retry on failure."""
    results = {}
    failed = []
    
    for table_id in table_ids:
        for attempt in range(max_retries):
            try:
                job = start_table_export(table_id, stack_url, token)
                completed_job = wait_for_export_job(job["job_id"], stack_url, token)
                
                # Download file
                filename = table_id.replace(".", "_") + ".csv"
                download_export_file(completed_job, filename)
                
                results[table_id] = filename
                print(f"✓ {table_id}")
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"✗ {table_id} failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"✗ {table_id} failed after {max_retries} attempts: {e}")
                    failed.append(table_id)
    
    print(f"\nCompleted: {len(results)}/{len(table_ids)}")
    if failed:
        print(f"Failed: {failed}")
    
    return results, failed
```
