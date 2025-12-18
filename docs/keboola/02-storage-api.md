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

#### Overview

Keboola Storage API supports pagination for different scenarios. Choose the right approach based on your use case:

| Use Case | Method | Max Records | Best For |
|----------|--------|-------------|----------|
| Quick data preview | `data-preview` with limit/offset | 1,000 rows | Testing, sampling |
| List resources | List endpoints with limit/offset | Unlimited | Browsing tables/buckets |
| Full table export | `export-async` | Unlimited | Production data export |

#### Data Preview Pagination

For quick data preview with small result sets, use limit/offset pagination:

```python
import requests
import os

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]
table_id = "in.c-main.customers"

def export_table_paginated(table_id, chunk_size=100):
    """Export table preview in chunks using limit/offset.
    
    Args:
        table_id: Table identifier (e.g., 'in.c-main.customers')
        chunk_size: Number of rows per request (max 1000)
    
    Returns:
        List of all rows (limited to 1000 total)
    """
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
        
        # Stop if we've reached the endpoint limit
        if len(all_data) >= 1000:
            break

    return all_data

# Usage
preview_data = export_table_paginated("in.c-main.customers", chunk_size=100)
print(f"Retrieved {len(preview_data)} rows")
```

**Important**: `data-preview` endpoint is limited to 1000 rows maximum. For larger datasets, use async export (see below).

#### API Response Pagination (List Operations)

Many API endpoints that return lists support pagination parameters:

```python
def list_all_tables_paginated():
    """List all tables with pagination support.
    
    Returns:
        List of all tables in the project
    """
    all_tables = []
    offset = 0
    limit = 100

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

# Usage
all_tables = list_all_tables_paginated()
for table in all_tables:
    print(f"{table['id']}: {table['rowsCount']} rows")
```

**Other endpoints that support pagination**:

```python
# List buckets
def list_all_buckets():
    all_buckets = []
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/buckets",
            headers={"X-StorageApi-Token": token},
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        buckets = response.json()
        
        if not buckets or len(buckets) == 0:
            break
        
        all_buckets.extend(buckets)
        
        if len(buckets) < limit:
            break
        
        offset += limit
    
    return all_buckets

# List jobs
def list_recent_jobs(max_jobs=1000):
    all_jobs = []
    offset = 0
    limit = 100
    
    while len(all_jobs) < max_jobs:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs",
            headers={"X-StorageApi-Token": token},
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        jobs = response.json()
        
        if not jobs:
            break
        
        all_jobs.extend(jobs)
        
        if len(jobs) < limit:
            break
        
        offset += limit
    
    return all_jobs[:max_jobs]
```

#### Pagination Parameters

Common pagination parameters across Keboola Storage API:

- **limit**: Number of records to return per request
  - Default: Varies by endpoint (typically 100)
  - Maximum: Varies by endpoint (typically 1000)
- **offset**: Number of records to skip from the beginning
  - Default: 0
  - Use case: Implement page-based navigation

```python
# Example: Get page 3 with 50 items per page
page = 3
page_size = 50

params = {
    "limit": page_size,
    "offset": (page - 1) * page_size  # Skip first 100 records
}

response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": token},
    params=params
)
```

#### Full Table Export (Recommended for Large Tables)

For exporting complete tables, especially large ones, use async export instead of pagination. The platform handles pagination internally:

```python
import time

def export_large_table(table_id, output_file="export.csv"):
    """Export large table using async job (handles pagination internally).
    
    Args:
        table_id: Table identifier
        output_file: Path to save exported data
    
    Returns:
        Path to exported file
    """
    # Start async export
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    print(f"Export job started: {job_id}")
    
    # Poll for completion
    timeout = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job_response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        job_response.raise_for_status()
        job = job_response.json()
        
        if job["status"] == "success":
            # Download complete file (all rows, pagination handled by Keboola)
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            with open(output_file, "wb") as f:
                f.write(data_response.content)
            
            print(f"Export complete: {output_file}")
            return output_file
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Export failed: {error_msg}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Export job {job_id} did not complete within {timeout}s")

# Usage
export_large_table("in.c-main.customers", "customers_full.csv")
```

#### When to Use Each Approach

**Use `data-preview` with pagination when**:
- Testing queries or data structure
- Sampling data for analysis
- Building UI with small result sets
- Need quick response times
- Working with ≤1000 rows

**Use list endpoints with pagination when**:
- Browsing available tables, buckets, or configurations
- Building admin interfaces
- Need to process all resources in batches
- Searching across resources

**Use `export-async` when**:
- Exporting complete tables for processing
- Working with >1000 rows
- Need all data for ETL/backup
- Performance is critical
- Building production data pipelines

#### Complete Pagination Example

Here's a complete example that demonstrates all pagination approaches:

```python
import requests
import os
import time
import csv

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

def preview_table_sample(table_id, sample_size=100):
    """Get small sample of table data."""
    response = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}/data-preview",
        headers={"X-StorageApi-Token": token},
        params={"limit": sample_size}
    )
    response.raise_for_status()
    return response.json()

def find_table_by_name(table_name_substring):
    """Search for tables by name using pagination."""
    matching_tables = []
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tables",
            headers={"X-StorageApi-Token": token},
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        tables = response.json()
        
        if not tables:
            break
        
        for table in tables:
            if table_name_substring.lower() in table['name'].lower():
                matching_tables.append(table)
        
        if len(tables) < limit:
            break
        
        offset += limit
    
    return matching_tables

def export_table_full(table_id, output_file):
    """Export complete table regardless of size."""
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
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
            file_url = job["results"]["file"]["url"]
            data_response = requests.get(file_url)
            
            with open(output_file, "wb") as f:
                f.write(data_response.content)
            
            # Count rows
            with open(output_file, "r") as f:
                row_count = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
            
            return row_count
        
        elif job["status"] in ["error", "cancelled", "terminated"]:
            raise Exception(f"Export failed: {job.get('error', {}).get('message')}")
        
        time.sleep(2)
    
    raise TimeoutError("Export timeout")

# Example workflow
if __name__ == "__main__":
    # 1. Quick preview
    print("Getting sample data...")
    sample = preview_table_sample("in.c-main.customers", 10)
    print(f"Sample: {len(sample)} rows")
    
    # 2. Find tables
    print("\nSearching for customer tables...")
    tables = find_table_by_name("customer")
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table['id']} ({table['rowsCount']} rows)")
    
    # 3. Export full table
    print("\nExporting full table...")
    row_count = export_table_full("in.c-main.customers", "customers_export.csv")
    print(f"Exported {row_count} rows to customers_export.csv")
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
