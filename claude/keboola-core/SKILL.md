# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/`
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-22T14:17:51.318430

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

### Token Scopes and Permissions

Storage API tokens have different permission scopes that control what operations they can perform:

#### Available Scopes

- **Read-only access** (`storage:read`):
  - List buckets and tables
  - Export table data
  - View table metadata
  - View configurations (read-only)
  - Cannot create, modify, or delete anything

- **Full access** (`storage:write`, `storage:read`):
  - All read operations
  - Create/delete buckets and tables
  - Import/write data
  - Manage table structure
  - Create and modify configurations

- **Configuration management** (`configurations:read`, `configurations:write`):
  - Read component configurations
  - Create/modify component configurations
  - Manage orchestrations

#### Creating Tokens with Specific Scopes

**Via Keboola UI**:
1. Go to **Users & Settings** → **API Tokens**
2. Click **New Token**
3. Enter token description
4. Select permissions:
   - **Read-only**: Check only "Read" boxes
   - **Full access**: Check all permission boxes
   - **Custom**: Select specific scopes needed
5. Set expiration date (optional but recommended)
6. Click **Create**

**Via API** (requires admin token):

```python
# Create read-only token
response = requests.post(
    f"https://{STACK_URL}/v2/storage/tokens",
    headers={"X-StorageApi-Token": admin_token},
    json={
        "description": "Read-only token for reporting",
        "expiresIn": 2592000,  # 30 days in seconds
        "canManageBuckets": False,
        "canReadAllFileUploads": True,
        "bucketPermissions": {
            "in.c-main": "read"
        }
    }
)
read_only_token = response.json()["token"]

# Create full access token
response = requests.post(
    f"https://{STACK_URL}/v2/storage/tokens",
    headers={"X-StorageApi-Token": admin_token},
    json={
        "description": "Full access token for ETL pipeline",
        "expiresIn": 7776000,  # 90 days
        "canManageBuckets": True,
        "canReadAllFileUploads": True,
        "bucketPermissions": {}  # Empty = all buckets
    }
)
full_access_token = response.json()["token"]
```

#### Bucket-Level Permissions

You can grant granular access to specific buckets:

```python
response = requests.post(
    f"https://{STACK_URL}/v2/storage/tokens",
    headers={"X-StorageApi-Token": admin_token},
    json={
        "description": "Limited access token",
        "canManageBuckets": False,
        "bucketPermissions": {
            "in.c-main": "read",      # Read-only access
            "out.c-reports": "write"   # Read and write access
        }
    }
)
```

**Permission levels**:
- `"read"`: Can list and export tables
- `"write"`: Can read + create/modify/delete tables

#### Security Best Practices

**DO**:

- Use **read-only tokens** for dashboards and reporting
- Use **full access tokens** only for ETL/data pipelines
- Set **expiration dates** on all tokens (30-90 days recommended)
- Create **separate tokens** for each application/service
- Use **bucket-specific permissions** when possible
- Store tokens in **environment variables**, never in code
- Rotate tokens regularly (every 90 days minimum)
- Use **descriptive names** to track token usage
- Revoke tokens immediately when no longer needed

**DON'T**:

- Share tokens between applications
- Commit tokens to version control
- Use master/admin tokens in production code
- Grant full access when read-only is sufficient
- Create tokens without expiration dates
- Reuse tokens across environments (dev/staging/prod)

#### Checking Token Permissions

Verify what your token can do:

```python
response = requests.get(
    f"https://{STACK_URL}/v2/storage/tokens/verify",
    headers={"X-StorageApi-Token": token}
)
token_info = response.json()

print(f"Token description: {token_info['description']}")
print(f"Can manage buckets: {token_info['canManageBuckets']}")
print(f"Bucket permissions: {token_info['bucketPermissions']}")
print(f"Expires: {token_info.get('expires', 'Never')}")
```

#### Common Permission Errors

```python
# Error: 403 Forbidden - Insufficient permissions
try:
    response = requests.post(
        f"https://{STACK_URL}/v2/storage/buckets",
        headers={"X-StorageApi-Token": read_only_token},
        json={"name": "new-bucket", "stage": "in"}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        print("Error: Token does not have write permissions")
        print("Solution: Use a token with canManageBuckets=True")
    raise
```

#### Use Case Examples

**Read-only dashboard token**:
```python
# For Streamlit apps, Data Apps, reporting tools
token_config = {
    "description": "Dashboard read-only access",
    "expiresIn": 2592000,  # 30 days
    "canManageBuckets": False,
    "bucketPermissions": {
        "in.c-analytics": "read",
        "in.c-sales": "read"
    }
}
```

**ETL pipeline token**:
```python
# For extractors, transformations, data loading
token_config = {
    "description": "ETL pipeline full access",
    "expiresIn": 7776000,  # 90 days
    "canManageBuckets": True,
    "bucketPermissions": {}  # All buckets
}
```

**Component development token**:
```python
# For local development and testing
token_config = {
    "description": "Dev environment token",
    "expiresIn": 2592000,  # 30 days
    "canManageBuckets": True,
    "bucketPermissions": {
        "in.c-dev": "write",
        "out.c-dev": "write"
    }
}
```

## Regional Stacks

Keboola operates multiple regional stacks:
- **US**: connection.keboola.com
- **EU**: connection.eu-central-1.keboola.com
- **Azure**: connection.north-europe.azure.keboola.com

Always use your project's stack URL, not a hardcoded one.

### Workspaces

Workspaces are temporary database environments (Snowflake, Redshift, or BigQuery) created for:
- **Data Apps**: Direct database access for analytics
- **Transformations**: SQL/Python data processing
- **Sandboxes**: Ad-hoc data exploration

**Key Concepts**:

- **Workspace ID**: Identifies a specific workspace instance (e.g., `12345`)
- **Project ID**: Identifies your Keboola project (e.g., `6789`)
- **Context**: Determines which API/connection to use

**Workspace vs Storage**:

| Aspect | Workspace | Storage |
|--------|-----------|--------|
| **Technology** | Snowflake/Redshift/BigQuery | Keboola Storage API |
| **Access Method** | Database connection (SQL) | REST API (HTTP) |
| **Use Case** | SQL queries, Data Apps | Data management, orchestration |
| **Persistence** | Temporary (auto-deleted) | Permanent |
| **Table Names** | `database.schema.table` | `bucket.table` |

**SQL Editor (Snowflake Workspaces)**:

Keboola has a built-in SQL Editor for Snowflake workspaces (currently in public beta):

- **Access**: Workspaces → Create Workspace → Snowflake SQL Workspace → SQL Editor tab
- **Features**: Query, explore, and test SQL directly in Keboola
- **Supported**: Snowflake workspaces only
- **Important**: Becoming essential as direct Snowflake access is deprecated for MT/PAYG customers (end of 2025)

References:
- [SQL Editor Documentation](https://help.keboola.com/workspace/sql-editor/)
- [SQL Editor Announcement](https://changelog.keboola.com/sql-editor-for-snowflake-sql-workspaces/)

**When to Use What**:

```python
# Use WORKSPACE when:
# - Running inside Data App (production)
# - Running transformation
# - Direct SQL queries needed
if 'KBC_PROJECT_ID' in os.environ:
    conn = st.connection('snowflake', type='snowflake')
    query = f'SELECT * FROM "{os.environ["KBC_PROJECT_ID"]}"."in.c-main"."customers"'
    df = conn.query(query)

# Use STORAGE API when:
# - Running outside Keboola (local development)
# - Managing tables/buckets
# - Orchestrating data flows
else:
    import requests
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/in.c-main.customers/export-async",
        headers={"X-StorageApi-Token": token}
    )
```


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

**Problem**: Polling async jobs incorrectly - too frequently, without proper timeout/error handling, or without cleanup

**Common Mistakes**:
- Polling too frequently (every 100ms) → Gets account rate-limited/banned
- Not handling all error states → Jobs fail silently
- Missing timeout logic → Scripts hang forever
- Not cleaning up failed jobs → Resource leaks

**Solution**: Poll with appropriate interval, handle all states, and clean up:

```python
import time
import requests

def wait_for_job(job_id, timeout=300, poll_interval=2):
    """Wait for job completion with proper polling and error handling.
    
    Args:
        job_id: Keboola job ID
        timeout: Maximum wait time in seconds (default 5 minutes)
        poll_interval: Seconds between status checks (minimum 2 seconds)
    
    Returns:
        Job result dict on success
    
    Raises:
        TimeoutError: Job didn't complete within timeout
        Exception: Job failed with error
    """
    # Enforce minimum poll interval to avoid rate limiting
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
                timeout=10  # Request timeout
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Network error - retry with backoff
            print(f"Request failed (attempt {attempts}): {e}")
            time.sleep(min(poll_interval * 2, 10))
            continue
        
        job = response.json()
        status = job["status"]
        
        # SUCCESS: Job completed successfully
        if status == "success":
            print(f"Job {job_id} completed successfully after {attempts} checks")
            return job
        
        # ERROR STATES: Job failed, was cancelled, or terminated
        elif status in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            error_type = job.get("error", {}).get("type", "unknown")
            
            # Log full error details
            print(f"Job {job_id} failed:")
            print(f"  Status: {status}")
            print(f"  Error Type: {error_type}")
            print(f"  Message: {error_msg}")
            
            raise Exception(
                f"Job {job_id} failed with status '{status}': {error_msg}"
            )
        
        # PROCESSING: Job still running (waiting, processing)
        elif status in ["waiting", "processing"]:
            elapsed = time.time() - start_time
            print(f"Job {job_id} status: {status} (elapsed: {elapsed:.1f}s)")
            time.sleep(poll_interval)
        
        # UNKNOWN STATE: Unexpected status
        else:
            print(f"Warning: Unknown job status '{status}' for job {job_id}")
            time.sleep(poll_interval)
    
    # TIMEOUT: Job didn't complete in time
    elapsed = time.time() - start_time
    raise TimeoutError(
        f"Job {job_id} did not complete within {timeout}s "
        f"(checked {attempts} times over {elapsed:.1f}s)"
    )


# Example usage with proper cleanup
def export_table_safe(table_id):
    """Export table with proper job polling and cleanup."""
    job_id = None
    
    try:
        # Start async export
        response = requests.post(
            f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
            headers={"X-StorageApi-Token": token}
        )
        response.raise_for_status()
        job_id = response.json()["id"]
        
        # Wait with proper polling (2-second intervals)
        job = wait_for_job(job_id, timeout=600, poll_interval=2)
        
        # Download result
        file_url = job["results"]["file"]["url"]
        data_response = requests.get(file_url)
        return data_response.content
        
    except TimeoutError as e:
        print(f"Export timed out: {e}")
        # Job might still be running - log for manual cleanup
        if job_id:
            print(f"Job ID for cleanup: {job_id}")
        raise
        
    except Exception as e:
        print(f"Export failed: {e}")
        # Job failed or was cancelled - already logged
        raise
```

**Real-World Example: Rate Limiting**

```python
# ❌ WRONG - Polls every 100ms, will get banned
def poll_too_fast(job_id):
    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        if response.json()["status"] == "success":
            return response.json()
        time.sleep(0.1)  # 100ms = 10 requests/second!

# ✅ CORRECT - Polls every 2 seconds (safe rate)
def poll_correctly(job_id):
    return wait_for_job(job_id, poll_interval=2)
```

**Polling Interval Guidelines**:

| Job Type | Typical Duration | Recommended Interval |
|----------|------------------|---------------------|
| Table export (small) | 5-30 seconds | 2 seconds |
| Table export (large) | 1-10 minutes | 3-5 seconds |
| Table import | 10-60 seconds | 2-3 seconds |
| Transformation | 30-300 seconds | 5 seconds |

**Why 2 seconds minimum?**
- Keboola rate limits: ~30 requests/minute per token
- Polling every 2 seconds = 30 requests/minute (safe)
- Polling every 100ms = 600 requests/minute (banned)

**Error States to Handle**:

```python
SUCCESS_STATES = ["success"]
ERROR_STATES = ["error", "cancelled", "terminated"]
PROCESSING_STATES = ["waiting", "processing"]

# Always check for ALL error states
if job["status"] in ERROR_STATES:
    # Extract detailed error information
    error_details = job.get("error", {})
    error_message = error_details.get("message", "Unknown error")
    error_type = error_details.get("type", "unknown")
    
    # Log for debugging
    logging.error(f"Job {job_id} failed: {error_type} - {error_message}")
    
    raise Exception(f"Job failed: {error_message}")
```
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



## 6. Incremental Loads Without Primary Key

**Problem**: Attempting incremental load on table without primary key

**Solution**: Always set primary key before using incremental mode:

```python
# ❌ WRONG - This will fail if table has no primary key
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": token},
    params={
        "incremental": "1",
        "dataString": csv_data
    }
)

# ✅ CORRECT - Set primary key first
# Option 1: Set when creating table
response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={"X-StorageApi-Token": token},
    params={
        "name": "my_table",
        "primaryKey": "id",  # Set primary key at creation
        "dataString": csv_data
    }
)

# Option 2: Set on existing table
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}",
    headers={"X-StorageApi-Token": token},
    json={"primaryKey": ["id"]}
)
response.raise_for_status()

# Now incremental loads will work
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": token},
    params={
        "incremental": "1",
        "dataString": new_data
    }
)
```

**Why**: Incremental mode needs primary key to identify which rows to update vs insert.

## 7. Using Wrong Endpoint for Table Import

**Problem**: Confusing table creation endpoint with table import endpoint

**Solution**: Use correct endpoint based on operation:

```python
# ❌ WRONG - Using creation endpoint for existing table
response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={"X-StorageApi-Token": token},
    params={
        "name": "existing_table",  # This creates NEW table or fails
        "dataString": csv_data
    }
)

# ✅ CORRECT - Use import endpoint for existing table
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": token},
    params={"dataString": csv_data}
)

# ✅ CORRECT - Use creation endpoint only for NEW tables
response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={"X-StorageApi-Token": token},
    params={
        "name": "new_table",
        "dataString": csv_data
    }
)
```

**Rule of thumb**:
- Creating new table: `/buckets/{bucket}/tables-async`
- Importing to existing table: `/tables/{table_id}/import-async`

## 8. Confusing Workspace Context with Project Context

**Problem**: Using workspace IDs in Storage API calls or Storage API table names in workspace SQL

**Solution**: Understand the context boundary:

```python
# ❌ WRONG - Using workspace-style table reference in Storage API
import requests
project_id = os.environ['KBC_PROJECT_ID']
table_ref = f'"{project_id}"."in.c-main"."customers"'  # Snowflake format

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_ref}/export-async",  # FAILS
    headers={"X-StorageApi-Token": token}
)

# ✅ CORRECT - Storage API uses bucket.table format (no project ID)
table_id = "in.c-main.customers"  # Storage API format
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

# ❌ WRONG - Using Storage API format in workspace SQL
import streamlit as st
conn = st.connection('snowflake', type='snowflake')
table_id = "in.c-main.customers"  # Storage API format

query = f"SELECT * FROM {table_id}"  # FAILS - not valid SQL
df = conn.query(query)

# ✅ CORRECT - Workspace SQL requires fully qualified names
project_id = os.environ['KBC_PROJECT_ID']
table_ref = f'"{project_id}"."in.c-main"."customers"'  # Snowflake format

query = f"SELECT * FROM {table_ref}"
df = conn.query(query)
```

**Rule of thumb**:
- **Storage API** (REST endpoints): Use `bucket.table` format, no project ID
- **Workspace** (SQL queries): Use `"PROJECT_ID"."bucket"."table"` format

**Why the difference?**

- Storage API operates at **project level** - it knows your project from the token
- Workspace operates at **database level** - PROJECT_ID is the database name in Snowflake

### Context Detection Pattern

```python
def get_table_reference(bucket, table):
    """Get correct table reference for current context."""
    if 'KBC_PROJECT_ID' in os.environ:
        # Workspace context - return Snowflake-qualified name
        project_id = os.environ['KBC_PROJECT_ID']
        return f'"{project_id}"."{bucket}"."{table}"'
    else:
        # Storage API context - return API format
        return f"{bucket}.{table}"

# Usage
table_ref = get_table_reference('in.c-main', 'customers')

if 'KBC_PROJECT_ID' in os.environ:
    # Workspace: Use in SQL
    query = f"SELECT * FROM {table_ref}"
    df = conn.query(query)
else:
    # Storage API: Use in endpoint
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_ref}/export-async",
        headers={"X-StorageApi-Token": token}
    )
```

**Common Error Messages**:

- `Table 'in.c-main.customers' does not exist` (in workspace) → Use quoted, qualified name
- `Invalid table ID` (in Storage API) → Remove quotes and project ID
- `SQL compilation error` (in workspace) → Missing quotes or project ID


## 9. Incorrect Pagination Usage

**Problem**: Using data-preview pagination for large table exports or not handling pagination in list endpoints

**Solution**: Choose the right pagination strategy for your use case:

```python
# ❌ WRONG - Using data-preview for large tables (limited to 1000 rows)
def export_large_table_wrong(table_id):
    offset = 0
    limit = 1000
    all_data = []
    
    while True:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tables/{table_id}/data-preview",
            headers={"X-StorageApi-Token": token},
            params={"limit": limit, "offset": offset}
        )
        data = response.json()
        if not data:
            break
        all_data.extend(data)
        offset += limit
    
    return all_data  # Will never get more than 1000 rows!

# ✅ CORRECT - Use async export for complete table data
def export_large_table_correct(table_id):
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # Poll and download (see full example in Storage API docs)
    # Returns complete dataset regardless of size
    return wait_for_export_job(job_id)

# ❌ WRONG - Not handling pagination in list endpoints
def get_all_tables_wrong():
    response = requests.get(
        f"https://{stack_url}/v2/storage/tables",
        headers={"X-StorageApi-Token": token}
    )
    return response.json()  # Only returns first page!

# ✅ CORRECT - Paginate through all results
def get_all_tables_correct():
    all_tables = []
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
        
        all_tables.extend(tables)
        
        if len(tables) < limit:
            break
        
        offset += limit
    
    return all_tables
```

**Rule of thumb**:
- **Small preview (<100 rows)**: Use `data-preview` without pagination
- **Browse/list resources**: Use pagination with `limit`/`offset`
- **Full table export**: Use `export-async` (no manual pagination needed)

**Why**: Different endpoints have different pagination capabilities and limits. Using the wrong approach can result in incomplete data or unnecessary complexity.



## 10. Using Tokens with Insufficient Permissions

**Problem**: API calls fail with 403 Forbidden because token lacks required permissions

**Solution**: Use appropriate token scope for your operation:

```python
# ❌ WRONG - Using read-only token for write operation
read_only_token = os.environ['KEBOOLA_READ_TOKEN']

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": read_only_token},
    params={"dataString": csv_data}
)
# Fails with 403 Forbidden

# ✅ CORRECT - Use token with write permissions
write_token = os.environ['KEBOOLA_WRITE_TOKEN']

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": write_token},
    params={"dataString": csv_data}
)
response.raise_for_status()

# ✅ BETTER - Check token permissions before operation
def verify_token_permissions(token, required_permission='write'):
    """Verify token has required permissions."""
    response = requests.get(
        f"https://{stack_url}/v2/storage/tokens/verify",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    token_info = response.json()
    
    if required_permission == 'write' and not token_info.get('canManageBuckets'):
        raise PermissionError(
            f"Token '{token_info['description']}' does not have write permissions. "
            "Create a token with canManageBuckets=True."
        )
    
    return token_info

# Usage
token_info = verify_token_permissions(write_token, 'write')
print(f"Using token: {token_info['description']}")
```

**Rule of thumb**:
- **Reading data**: Use tokens with `storage:read` or bucket-specific read permissions
- **Writing data**: Use tokens with `canManageBuckets=True` and write permissions
- **Production apps**: Use least-privilege tokens (read-only when possible)
- **Development**: Use separate dev tokens with appropriate scope

**Common scenarios**:

```python
# Scenario 1: Dashboard/Data App (read-only)
READ_TOKEN = os.environ['KEBOOLA_READ_TOKEN']  # read permissions only
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": READ_TOKEN}
)  # ✓ Works - export only needs read permission

# Scenario 2: ETL Pipeline (read + write)
WRITE_TOKEN = os.environ['KEBOOLA_WRITE_TOKEN']  # full permissions
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": WRITE_TOKEN},
    params={"dataString": data}
)  # ✓ Works - import needs write permission

# Scenario 3: Bucket-specific access
LIMITED_TOKEN = os.environ['KEBOOLA_LIMITED_TOKEN']  # only in.c-main access
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/in.c-main.customers/export-async",
    headers={"X-StorageApi-Token": LIMITED_TOKEN}
)  # ✓ Works - has access to in.c-main bucket

response = requests.post(
    f"https://{stack_url}/v2/storage/tables/in.c-sales.orders/export-async",
    headers={"X-StorageApi-Token": LIMITED_TOKEN}
)  # ✗ Fails - no access to in.c-sales bucket
```

**Why**: Using the principle of least privilege improves security. Read-only tokens can't accidentally modify data, and bucket-specific tokens limit blast radius if compromised.

## 6. Authentication Errors

### Invalid Token (401 Unauthorized)

**Problem**: Getting 401 errors when making API calls

**Common Causes**:

1. **Token not set or incorrect**:
```python
# ❌ WRONG - Token not loaded
headers = {"X-StorageApi-Token": ""}

# ✅ CORRECT - Load from environment
import os
token = os.environ.get("KEBOOLA_TOKEN")
if not token:
    raise ValueError("KEBOOLA_TOKEN environment variable not set")

headers = {"X-StorageApi-Token": token}
```

2. **Token expired**:
```python
def check_token_expiration(token, stack_url):
    """Check if token is valid and when it expires."""
    try:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tokens/verify",
            headers={"X-StorageApi-Token": token}
        )
        response.raise_for_status()
        
        token_info = response.json()
        expires = token_info.get('expires')
        
        if expires:
            from datetime import datetime
            expiry_date = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            print(f"Token expires: {expiry_date}")
            
            if datetime.now(expiry_date.tzinfo) > expiry_date:
                raise Exception("Token has expired. Create a new token in Keboola UI.")
        else:
            print("Token does not expire")
        
        return token_info
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception(
                "Invalid token. Check that:\n"
                "1. Token is copied correctly (no extra spaces)\n"
                "2. Token hasn't been deleted in Keboola UI\n"
                "3. Token hasn't expired"
            )
        raise

# Usage
check_token_expiration(token, stack_url)
```

3. **Wrong stack URL**:
```python
# ❌ WRONG - Hardcoded wrong stack
stack_url = "connection.keboola.com"  # Your project might be on EU stack

# ✅ CORRECT - Use environment variable
stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")

# ✅ VERIFY - Test token on correct stack
response = requests.get(
    f"https://{stack_url}/v2/storage/tokens/verify",
    headers={"X-StorageApi-Token": token}
)
if response.status_code == 401:
    print(f"Token invalid for stack: {stack_url}")
    print("Check your project's stack URL in Keboola UI")
```

### Permission Denied (403 Forbidden)

**Problem**: Token is valid but operation is not allowed

**Solution**: Verify token has required permissions

```python
def diagnose_permission_error(token, stack_url, operation):
    """Diagnose why operation is forbidden."""
    response = requests.get(
        f"https://{stack_url}/v2/storage/tokens/verify",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    token_info = response.json()
    
    print(f"Token: {token_info['description']}")
    print(f"Can manage buckets: {token_info.get('canManageBuckets', False)}")
    print(f"Bucket permissions: {token_info.get('bucketPermissions', {})}")
    
    if operation == 'write' and not token_info.get('canManageBuckets'):
        print("\n❌ ERROR: Token lacks write permissions")
        print("SOLUTION: Create a new token with 'Manage Buckets' enabled")
        return False
    
    if operation == 'read' and not token_info.get('bucketPermissions'):
        print("\n❌ ERROR: Token has no bucket access")
        print("SOLUTION: Grant bucket-specific read permissions")
        return False
    
    return True

# Usage
try:
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
        headers={"X-StorageApi-Token": token},
        params={"dataString": csv_data}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        diagnose_permission_error(token, stack_url, 'write')
    raise
```

### Token Scope Issues

**Problem**: Token has wrong scope for the operation

**Solution**: Use appropriate token type

```python
# ❌ WRONG - Using read-only token for data import
READ_TOKEN = os.environ['KEBOOLA_READ_TOKEN']
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": READ_TOKEN},  # Will fail with 403
    params={"dataString": data}
)

# ✅ CORRECT - Use write token for imports
WRITE_TOKEN = os.environ['KEBOOLA_WRITE_TOKEN']
response = requests.post(
    f"https://{stack_url}/v2/storage/tables/{table_id}/import-async",
    headers={"X-StorageApi-Token": WRITE_TOKEN},
    params={"dataString": data}
)

# ✅ BEST - Validate token scope before operation
def get_appropriate_token(operation):
    """Get token with appropriate permissions."""
    if operation in ['write', 'import', 'create', 'delete']:
        token = os.environ.get('KEBOOLA_WRITE_TOKEN')
        if not token:
            raise ValueError(
                "Write operation requires KEBOOLA_WRITE_TOKEN. "
                "Set environment variable with a token that has write permissions."
            )
    else:
        token = os.environ.get('KEBOOLA_READ_TOKEN') or os.environ.get('KEBOOLA_TOKEN')
        if not token:
            raise ValueError("No Keboola token found in environment variables")
    
    return token

# Usage
token = get_appropriate_token('import')
```

### Network and Proxy Issues

**Problem**: Authentication fails due to network configuration

**Solution**: Configure requests properly for your network

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retry():
    """Create session with retry logic and proxy support."""
    session = requests.Session()
    
    # Configure retries
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    # Configure proxy if needed
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
    
    # Set timeout
    session.timeout = 30
    
    return session

# Usage
session = create_session_with_retry()

try:
    response = session.get(
        f"https://{stack_url}/v2/storage/tokens/verify",
        headers={"X-StorageApi-Token": token},
        timeout=30
    )
    response.raise_for_status()
    print("Authentication successful")
except requests.exceptions.Timeout:
    print("Request timed out. Check network connectivity.")
except requests.exceptions.ProxyError:
    print("Proxy error. Check HTTP_PROXY/HTTPS_PROXY environment variables.")
except requests.exceptions.SSLError:
    print("SSL error. Check certificate configuration.")
except requests.exceptions.ConnectionError:
    print(f"Cannot connect to {stack_url}. Check internet connection.")
```

### Complete Authentication Troubleshooting Function

```python
def troubleshoot_authentication(token, stack_url):
    """Complete authentication diagnostics."""
    print("=== Keboola Authentication Troubleshooting ===")
    
    # 1. Check token is set
    if not token:
        print("❌ No token provided")
        print("SOLUTION: Set KEBOOLA_TOKEN environment variable")
        return False
    
    print(f"✓ Token is set (length: {len(token)})")
    
    # 2. Check stack URL format
    if not stack_url.startswith(('connection.', 'http')):
        print(f"❌ Invalid stack URL format: {stack_url}")
        print("SOLUTION: Use format like 'connection.keboola.com'")
        return False
    
    print(f"✓ Stack URL format valid: {stack_url}")
    
    # 3. Test connectivity
    try:
        response = requests.get(
            f"https://{stack_url}/v2/storage",
            timeout=10
        )
        print(f"✓ Can reach stack (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach stack: {e}")
        print("SOLUTION: Check internet connection and firewall settings")
        return False
    
    # 4. Verify token
    try:
        response = requests.get(
            f"https://{stack_url}/v2/storage/tokens/verify",
            headers={"X-StorageApi-Token": token},
            timeout=10
        )
        response.raise_for_status()
        
        token_info = response.json()
        print(f"✓ Token is valid")
        print(f"  Description: {token_info.get('description', 'N/A')}")
        print(f"  Can manage buckets: {token_info.get('canManageBuckets', False)}")
        
        expires = token_info.get('expires')
        if expires:
            print(f"  Expires: {expires}")
        else:
            print(f"  Expires: Never")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Token is invalid (401 Unauthorized)")
            print("POSSIBLE CAUSES:")
            print("  1. Token was deleted in Keboola UI")
            print("  2. Token has expired")
            print("  3. Token is for different stack")
            print("  4. Token contains typos or extra whitespace")
            print("SOLUTION: Create a new token in Keboola UI (Users & Settings → API Tokens)")
        else:
            print(f"❌ Unexpected error: {e.response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False

# Usage
if not troubleshoot_authentication(token, stack_url):
    sys.exit(1)
```

### Quick Reference: Authentication Error Codes

| Error Code | Meaning | Common Cause | Solution |
|------------|---------|--------------|----------|
| 401 | Unauthorized | Invalid/expired token | Verify token, create new one if expired |
| 403 | Forbidden | Insufficient permissions | Use token with write/manage permissions |
| 404 | Not Found | Wrong stack URL or table doesn't exist | Verify stack URL and table ID |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff |
| 500 | Server Error | Keboola platform issue | Retry with backoff, check status page |

## Storage vs Workspace Context


---

<!-- Source: 04-component-development.md -->

# Component Development

## Overview

Keboola components are Docker containers that follow the Common Interface specification for processing data. They communicate with Keboola exclusively through the filesystem at `/data`.

## Component Types

- **Extractors**: Pull data from external sources
- **Writers**: Send data to external destinations
- **Applications**: Process or transform data

Note: Don't include component type names ('extractor', 'writer', 'application') in the component name itself.

## Project Structure

```
my-component/
├── src/
│   ├── component.py          # Main logic with run() function
│   └── configuration.py      # Configuration validation
├── component_config/
│   ├── component_config.json           # Configuration schema
│   ├── component_long_description.md   # Detailed docs
│   └── component_short_description.md  # Brief description
├── tests/
│   └── test_component.py     # Unit tests
├── data/                     # Local data folder (gitignored)
│   ├── config.json           # Example config for local testing
│   ├── in/                   # Input tables and files
│   └── out/                  # Output tables and files
├── .github/workflows/
│   └── push.yml              # CI/CD deployment
├── Dockerfile                # Container definition
└── pyproject.toml            # Python dependencies
```

## Data Folder Contract

Components communicate with Keboola through the `/data` directory:

**INPUT** (read-only):
- `config.json` - Component configuration from UI
- `in/tables/*.csv` - Input tables with `.manifest` files
- `in/files/*` - Input files
- `in/state.json` - Previous run state (for incremental processing)

**OUTPUT** (write):
- `out/tables/*.csv` - Output tables with `.manifest` files
- `out/files/*` - Output files
- `out/state.json` - New state for next run

**IMPORTANT**: The Keboola platform automatically creates all data directories (`data/in/`, `data/out/tables/`, `data/out/files/`, etc.). You **never** need to call `mkdir()` or create these directories manually in your component code.

## Basic Component Implementation

```python
from keboola.component import CommonInterface
import logging
import sys
import traceback

REQUIRED_PARAMETERS = ['api_key', 'endpoint']

class Component(CommonInterface):
    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # 1. Validate configuration
            self.validate_configuration(REQUIRED_PARAMETERS)
            params = self.configuration.parameters

            # 2. Load state for incremental processing
            state = self.get_state_file()
            last_timestamp = state.get('last_timestamp')

            # 3. Process input tables
            input_tables = self.get_input_tables_definitions()
            for table in input_tables:
                self._process_table(table)

            # 4. Create output tables with manifests
            self._create_output_tables()

            # 5. Save state for next run
            self.write_state_file({
                'last_timestamp': current_timestamp
            })

        except ValueError as err:
            # User errors (configuration/input issues)
            logging.error(str(err))
            print(err, file=sys.stderr)
            sys.exit(1)
        except Exception as err:
            # System errors (unhandled exceptions)
            logging.exception("Unhandled error occurred")
            traceback.print_exc(file=sys.stderr)
            sys.exit(2)

if __name__ == '__main__':
    try:
        comp = Component()
        comp.run()
    except Exception as e:
        logging.exception("Component execution failed")
        sys.exit(2)
```

## Configuration Schema

Define configuration parameters in `component_config/component_config.json`:

```json
{
  "type": "object",
  "title": "Configuration",
  "required": ["api_key", "endpoint"],
  "properties": {
    "#api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your API authentication token",
      "format": "password"
    },
    "endpoint": {
      "type": "string",
      "title": "API Endpoint",
      "description": "Base URL for the API"
    },
    "incremental": {
      "type": "boolean",
      "title": "Incremental Load",
      "description": "Only fetch data since last run",
      "default": false
    }
  }
}
```

### Sensitive Data Handling

Prefix parameter names with `#` to enable automatic hashing:
```json
{
  "#password": {
    "type": "string",
    "title": "Password",
    "format": "password"
  }
}
```

### UI Elements

**Code Editor** (ACE editor for multi-line input):
```json
{
  "query": {
    "type": "string",
    "title": "SQL Query",
    "format": "textarea",
    "options": {
      "ace": {
        "mode": "sql"
      }
    }
  }
}
```

**Test Connection Button**:
```json
{
  "test_connection": {
    "type": "button",
    "title": "Test Connection",
    "options": {
      "syncAction": "test-connection"
    }
  }
}
```

## CSV Processing

Always process CSV files efficiently using generators:

```python
import csv

def process_input_table(table_def):
    with open(table_def.full_path, 'r', encoding='utf-8') as in_file:
        # Handle null characters with generator
        lazy_lines = (line.replace('\0', '') for line in in_file)
        reader = csv.DictReader(lazy_lines, dialect='kbc')

        for row in reader:
            # Process row by row for memory efficiency
            yield process_row(row)
```

## Creating Output Tables

Create output tables with proper schema definitions:

```python
from collections import OrderedDict
from keboola.component.dao import ColumnDefinition, BaseType

# Define schema
schema = OrderedDict({
    "id": ColumnDefinition(
        data_types=BaseType.integer(),
        primary_key=True
    ),
    "name": ColumnDefinition(),
    "value": ColumnDefinition(
        data_types=BaseType.numeric(length="10,2")
    )
})

# Create table definition
out_table = self.create_out_table_definition(
    name="results.csv",
    destination="out.c-data.results",
    schema=schema,
    incremental=True
)

# Write data
import csv
with open(out_table.full_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=out_table.column_names)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

# Write manifest
self.write_manifest(out_table)
```

## State Management for Incremental Processing

Implement proper state handling for incremental loads:

```python
def run_incremental(self):
    # Load previous state
    state = self.get_state_file()
    last_timestamp = state.get('last_timestamp', '1970-01-01T00:00:00Z')

    # Fetch only new data since last_timestamp
    new_data = self._fetch_data_since(last_timestamp)

    # Process and save data
    self._process_data(new_data)

    # Update state with current timestamp
    from datetime import datetime, timezone
    current_timestamp = datetime.now(timezone.utc).isoformat()
    self.write_state_file({
        'last_timestamp': current_timestamp,
        'records_processed': len(new_data)
    })
```

## Error Handling

Follow Keboola's error handling conventions:

- **Exit code 1**: User errors (configuration problems, invalid inputs)
- **Exit code 2**: System errors (unhandled exceptions, application errors)

```python
try:
    # Component logic
    validate_inputs(params)
    result = perform_operation()

except ValueError as err:
    # User-fixable errors
    logging.error(f"Configuration error: {err}")
    print(err, file=sys.stderr)
    sys.exit(1)

except requests.HTTPError as err:
    # API errors
    logging.error(f"API request failed: {err}")
    print(f"Failed to connect to API: {err.response.status_code}", file=sys.stderr)
    sys.exit(1)

except Exception as err:
    # Unhandled exceptions
    logging.exception("Unhandled error in component execution")
    traceback.print_exc(file=sys.stderr)
    sys.exit(2)
```

## Local Development

### Running Locally

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Set data directory environment variable
export KBC_DATADIR=./data

# Run component
python src/component.py
```

### Using Docker

```bash
# Build image
docker build -t my-component:latest .

# Run with mounted data folder
docker run --rm \
  -v $(pwd)/data:/data \
  -e KBC_DATADIR=/data \
  my-component:latest
```

### Prepare Test Data

Create `data/config.json` with example parameters:

```json
{
  "parameters": {
    "api_key": "your_key_here",
    "#password": "test_password",
    "from_date": "2024-01-01",
    "incremental": false
  }
}
```

Create sample input tables:

```bash
mkdir -p data/in/tables
cat > data/in/tables/input.csv <<EOF
id,name,email
1,John Doe,john@example.com
2,Jane Smith,jane@example.com
EOF
```

## Best Practices

### DO:

- Use `CommonInterface` class for all Keboola interactions
- Validate configuration early with `validate_configuration()`
- Process CSV files with generators for memory efficiency
- Always specify `encoding='utf-8'` for file operations
- Use proper exit codes (1 for user errors, 2 for system errors)
- Define explicit schemas for output tables
- Implement state management for incremental processing
- Write comprehensive tests
- Quote all SQL identifiers (`"column_name"`, not `column_name`)

### DON'T:

- Load entire CSV files into memory
- Hard-code configuration values
- Skip configuration validation
- Forget to write manifests for output tables
- Skip state file management for incremental loads
- Forget to handle null characters in CSV files
- Call `mkdir()` for platform-managed directories (in/, out/, tables/, files/)

## Dockerfile

```dockerfile
FROM python:3.11-alpine

# Install dependencies
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ /code/src/

# Set entrypoint with unbuffered output
ENTRYPOINT ["python", "-u", "/code/src/component.py"]
```

## CI/CD Deployment

### GitHub Actions Workflow

```yaml
# .github/workflows/push.yml
name: Build and Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t my-component:${{ github.ref_name }} .

      - name: Run tests
        run: docker-compose run --rm test

      - name: Deploy to Keboola
        env:
          KBC_DEVELOPERPORTAL_USERNAME: ${{ secrets.KBC_USERNAME }}
          KBC_DEVELOPERPORTAL_PASSWORD: ${{ secrets.KBC_PASSWORD }}
        run: ./deploy.sh
```

### Version Management

Follow semantic versioning:

- **v1.0.0** - Major release (breaking changes)
- **v1.1.0** - Minor release (new features)
- **v1.0.1** - Patch release (bug fixes)

```bash
# Tag and push
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Testing

### Unit Tests

```python
import unittest
from src.component import Component

class TestComponent(unittest.TestCase):
    def test_configuration_validation(self):
        """Test that required parameters are validated."""
        # Test implementation

    def test_csv_processing(self):
        """Test CSV reading and writing with proper encoding."""
        # Test implementation

    def test_state_management(self):
        """Test state file persistence."""
        # Test implementation
```

Run tests:

```bash
# Using unittest
python -m unittest discover -s tests

# Using pytest
pytest tests/ -v --cov=src
```

### Testing GitHub Actions Workflows

When developing components with CI/CD pipelines, test your workflows properly:

**Test workflow triggers locally** using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test push workflow
act push

# Test pull_request workflow
act pull_request

# Test with specific event
act workflow_dispatch
```

**Test workflow_run trigger pattern**:

```yaml
# .github/workflows/deploy.yml
name: Deploy Component

on:
  workflow_run:
    workflows: ["CI Tests"]
    types:
      - completed
    branches:
      - main

jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Keboola
        run: ./deploy.sh
```

**Best practices for workflow testing**:

- Use `pull_request` trigger for PR validation
- Use `workflow_run` for sequential workflows (e.g., test → deploy)
- Use `workflow_dispatch` for manual testing
- Always check `workflow_run.conclusion` before dependent jobs
- Test with branch protection rules enabled
- Verify secrets are properly scoped

**Debug workflow issues**:

```yaml
# Add debug step to workflows
- name: Debug workflow context
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Workflow run conclusion: ${{ github.event.workflow_run.conclusion }}"
```

## Code Quality

Use Ruff for code formatting and linting:

```bash
# Format code
ruff format .

# Lint and auto-fix issues
ruff check --fix .
```

## Resources

- [Keboola Developer Docs](https://developers.keboola.com/)
- [Python Component Library](https://github.com/keboola/python-component)
- [Component Tutorial](https://developers.keboola.com/extend/component/tutorial/)
- [Cookiecutter Template](https://github.com/keboola/cookiecutter-python-component)


---

<!-- Source: 05-dataapp-development.md -->

# Data App Development

## Overview

Keboola Data Apps are Streamlit applications that run directly in the Keboola platform, providing interactive dashboards and analytics tools. They connect to Keboola Storage and can query data from workspace tables.

## Key Concepts

### What are Data Apps?

Data Apps are containerized Streamlit applications that:
- Run inside Keboola's infrastructure
- Have direct access to project data via workspace
- Support interactive filtering, visualization, and exploration
- Can be shared with team members
- Auto-scale based on usage

### Architecture Pattern: SQL-First

**Core Principle**: Push computation to the database, never load large datasets into Python.

Why?
- Keboola workspaces (Snowflake, Redshift, BigQuery) are optimized for queries
- Loading data into Streamlit doesn't scale
- SQL aggregation is 10-100x faster than pandas

## Project Structure

```
my-dataapp/
├── streamlit_app.py          # Main app entry point with sidebar
├── pages/
│   ├── 01_Overview.py        # First page
│   ├── 02_Analytics.py       # Second page
│   └── 03_Details.py         # Third page
├── utils/
│   ├── data_loader.py        # Centralized data access
│   └── config.py             # Environment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

## Environment Setup

### Local Development

Data apps must work in two environments with **different contexts**:

1. **Local Development (Storage API / Project Context)**: 
   - Uses Storage API token for authentication
   - References tables as `in.c-bucket.table`
   - Exports data via REST API
   - No workspace ID involved

2. **Production (Workspace Context)**: 
   - Uses workspace database connection
   - References tables as `"PROJECT_ID"."in.c-bucket"."table"`
   - Queries data via SQL
   - Requires workspace environment variables

**Why Two Contexts?**

In production, Data Apps run inside a **Keboola workspace** (Snowflake/Redshift instance) where your project data is mirrored. This provides:
- Direct SQL access (fast queries)
- No API rate limits
- Native database features

During local development, you don't have workspace access, so you use the **Storage API** (REST) to export data.

**Environment Variables by Context**:

```bash
# WORKSPACE CONTEXT (Production)
# Automatically set by Keboola platform:
KBC_PROJECT_ID=6789           # Your project ID (used in table references)
KBC_BUCKET_ID=in.c-main       # Default bucket for app
KBC_TABLE_NAME=customers      # Default table for app

# STORAGE API CONTEXT (Local)
# You must set manually:
KEBOOLA_TOKEN=your-token                        # Storage API token
KEBOOLA_STACK_URL=connection.keboola.com       # Your stack URL
```

```python
# utils/config.py
import os
import streamlit as st

def get_connection_mode():
    """Detect if running locally or in Keboola."""
    return 'workspace' if 'KBC_PROJECT_ID' in os.environ else 'local'

def get_storage_token():
    """Get Storage API token from environment."""
    return os.environ.get('KEBOOLA_TOKEN')

def get_stack_url():
    """Get Keboola stack URL."""
    return os.environ.get('KEBOOLA_STACK_URL', 'connection.keboola.com')
```

### Connection Setup

```python
# utils/data_loader.py
import os
import streamlit as st
from utils.config import get_connection_mode

@st.cache_resource
def get_connection():
    """Get database connection based on environment."""
    mode = get_connection_mode()

    if mode == 'workspace':
        # Running in Keboola - use workspace connection
        return st.connection('snowflake', type='snowflake')
    else:
        # Local development - use Storage API
        return None  # Implement Storage API wrapper

def get_table_name():
    """Get fully qualified table name."""
    mode = get_connection_mode()

    if mode == 'workspace':
        # In workspace: database.schema.table
        return f'"{os.environ["KBC_PROJECT_ID"]}"."{os.environ["KBC_BUCKET_ID"]}"."{os.environ["KBC_TABLE_NAME"]}"'
    else:
        # Local: bucket.table
        return 'in.c-analysis.usage_data'
```

## SQL-First Design Pattern

### Good Pattern: Aggregate in Database

```python
@st.cache_data(ttl=300)
def get_summary_metrics(where_clause: str = ""):
    query = f'''
        SELECT
            COUNT(*) as total_count,
            COUNT(DISTINCT "user_id") as unique_users,
            AVG("session_duration") as avg_duration,
            SUM("revenue") as total_revenue
        FROM {get_table_name()}
        WHERE "date" >= CURRENT_DATE - INTERVAL '90 days'
            {f"AND {where_clause}" if where_clause else ""}
    '''
    return execute_query(query)
```

### Bad Pattern: Load All Data

```python
# DON'T DO THIS
df = execute_query(f"SELECT * FROM {get_table_name()}")
result = df.groupby('category').agg({'value': 'mean'})
```

## Global Filter Pattern

Global filters allow users to filter all pages from one control in the sidebar.

### Step 1: Create Filter Function

```python
# utils/data_loader.py
import streamlit as st

def get_user_type_filter_clause():
    """Get SQL WHERE clause for user type filter."""
    # Initialize session state with default
    if 'user_filter' not in st.session_state:
        st.session_state.user_filter = 'external'

    # Return appropriate SQL condition
    if st.session_state.user_filter == 'external':
        return '"user_type" = \'External User\''
    elif st.session_state.user_filter == 'internal':
        return '"user_type" = \'Keboola User\''
    return ''  # 'all' - no filter
```

### Step 2: Add UI Control

```python
# streamlit_app.py (sidebar)
import streamlit as st
from utils.data_loader import get_user_type_filter_clause

st.set_page_config(page_title="My Dashboard", layout="wide")

# Initialize session state
if 'user_filter' not in st.session_state:
    st.session_state.user_filter = 'external'

# Sidebar filter
st.sidebar.header("Filters")
user_option = st.sidebar.radio(
    "User Type:",
    options=['external', 'internal', 'all'],
    index=['external', 'internal', 'all'].index(st.session_state.user_filter)
)

# Update session state and trigger rerun if changed
if user_option != st.session_state.user_filter:
    st.session_state.user_filter = user_option
    st.rerun()
```

### Step 3: Use Filter in Pages

```python
# pages/01_Overview.py
import streamlit as st
from utils.data_loader import get_user_type_filter_clause, execute_query

# Build WHERE clause
where_parts = ['"status" = \'active\'']  # Base filter
user_filter = get_user_type_filter_clause()
if user_filter:
    where_parts.append(user_filter)
where_clause = ' AND '.join(where_parts)

# Use in query
@st.cache_data(ttl=300)
def get_page_data():
    query = f'''
        SELECT "date", COUNT(*) as count
        FROM {get_table_name()}
        WHERE {where_clause}
        GROUP BY "date"
        ORDER BY "date"
    '''
    return execute_query(query)

df = get_page_data()
st.line_chart(df, x='date', y='count')
```

## Query Execution

### Basic Query Function

```python
# utils/data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=300)
def execute_query(sql: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    conn = get_connection()

    try:
        df = conn.query(sql)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
```

### SQL Best Practices

**Always quote identifiers**:
```sql
-- CORRECT
SELECT "user_id", "revenue" FROM "my_table"

-- WRONG (fails with reserved keywords or mixed case)
SELECT user_id, revenue FROM my_table
```

**Use parameterized WHERE clauses**:
```python
def get_date_filter_clause(start_date, end_date):
    """Generate date range filter."""
    return f'"date" BETWEEN \'{start_date}\' AND \'{end_date}\''
```

## Caching Strategy

### Cache Database Connections

```python
@st.cache_resource
def get_connection():
    """Cache connection object (doesn't change)."""
    return st.connection('snowflake', type='snowflake')
```

### Cache Query Results

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_metrics(where_clause: str):
    """Cache query results (data can change)."""
    query = f"SELECT COUNT(*) FROM {get_table_name()} WHERE {where_clause}"
    return execute_query(query)
```

### TTL Guidelines

- **Static reference data**: `ttl=3600` (1 hour)
- **Dashboard metrics**: `ttl=300` (5 minutes)
- **Real-time data**: `ttl=60` (1 minute)
- **User-specific data**: No cache or very short TTL

## Session State Management

Streamlit reruns the entire script on every interaction. Use session state to persist values.

### Initialize Before Use

```python
# Always initialize session state before creating widgets
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = 'all'

# Now create widget
category = st.selectbox(
    "Category",
    options=['all', 'sales', 'marketing'],
    index=['all', 'sales', 'marketing'].index(st.session_state.selected_category)
)

# Update session state if changed
if category != st.session_state.selected_category:
    st.session_state.selected_category = category
    st.rerun()
```

## Error Handling

### Handle Empty Results

```python
df = get_page_data()

if df.empty:
    st.warning("No data available for the selected filters.")
else:
    st.line_chart(df, x='date', y='count')
```

### Catch Query Errors

```python
@st.cache_data(ttl=300)
def execute_query(sql: str):
    try:
        conn = get_connection()
        return conn.query(sql)
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()
```

## Common Patterns

### Metric Cards

```python
@st.cache_data(ttl=300)
def get_kpi_metrics():
    query = f'''
        SELECT
            COUNT(*) as total_users,
            SUM("revenue") as total_revenue,
            AVG("session_duration") as avg_duration
        FROM {get_table_name()}
        WHERE "date" >= CURRENT_DATE - INTERVAL '30 days'
    '''
    return execute_query(query).iloc[0]

metrics = get_kpi_metrics()

col1, col2, col3 = st.columns(3)
col1.metric("Total Users", f"{metrics['total_users']:,}")
col2.metric("Revenue", f"${metrics['total_revenue']:,.2f}")
col3.metric("Avg Duration", f"{metrics['avg_duration']:.1f}s")
```

### Date Range Filter

```python
import datetime

col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = col2.date_input("End Date", datetime.date.today())

where_clause = f'"date" BETWEEN \'{start_date}\' AND \'{end_date}\''
```

### Dynamic Dropdown

```python
@st.cache_data(ttl=3600)
def get_categories():
    query = f'SELECT DISTINCT "category" FROM {get_table_name()} ORDER BY "category"'
    return execute_query(query)['category'].tolist()

categories = get_categories()
selected = st.selectbox("Category", options=['All'] + categories)
```

## Variable Naming Conventions

### Avoid Naming Conflicts

**Problem**: Using same variable name for SQL clause and UI widget
```python
# DON'T DO THIS
user_filter = get_user_filter_clause()  # SQL string
user_filter = st.radio("User Type", ...)  # UI widget - overwrites SQL!
```

**Solution**: Use descriptive, unique names
```python
# DO THIS
user_filter_sql = get_user_filter_clause()  # SQL string
user_filter_option = st.radio("User Type", ...)  # UI widget
```

### Session State Keys

Use consistent, descriptive keys:
```python
# Good
st.session_state.user_type_filter = 'external'
st.session_state.selected_date_range = (start, end)
st.session_state.page_number = 1

# Bad (ambiguous)
st.session_state.filter = 'external'
st.session_state.data = (start, end)
st.session_state.page = 1
```

## Deployment

### Requirements File

```txt
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
snowflake-connector-python>=3.0.0
plotly>=5.17.0
```

### Environment Variables

Required in Keboola deployment:
- `KBC_PROJECT_ID` - Automatically set by platform
- `KBC_BUCKET_ID` - Automatically set by platform
- `KEBOOLA_TOKEN` - Set in Data App configuration
- `KEBOOLA_STACK_URL` - Set in Data App configuration

### Testing Before Deployment

```bash
# Local testing
export KEBOOLA_TOKEN=your_token
export KEBOOLA_STACK_URL=connection.keboola.com
streamlit run streamlit_app.py
```

## Best Practices

### DO:

- Always validate data schemas before writing code
- Push computation to database - aggregate in SQL, not Python
- Use fully qualified table names from `get_table_name()`
- Quote all identifiers in SQL (`"column_name"`)
- Cache all queries with `@st.cache_data(ttl=300)`
- Centralize data access in `utils/data_loader.py`
- Initialize session state with defaults before UI controls
- Use unique, descriptive variable names
- Test visually before deploying
- Handle empty DataFrames gracefully
- Support both local and production environments

### DON'T:

- Skip data validation - always check schemas first
- Load large datasets into Python - aggregate in database
- Hardcode table names - use `get_table_name()` function
- Use same variable name twice (SQL clause and UI widget)
- Forget session state initialization before creating widgets
- Assume columns exist - validate first
- Use unquoted SQL identifiers
- Skip error handling for empty query results
- Deploy without local testing

## Visual Verification Workflow

Before deploying, test your app:

1. **Start local server**: `streamlit run streamlit_app.py`
2. **Open in browser**: `http://localhost:8501`
3. **Test all interactions**:
   - Click through all pages
   - Try all filter combinations
   - Verify metrics update correctly
   - Check for error messages
4. **Capture screenshots** of working features
5. **Deploy with confidence**

## Common Issues

### "KeyError: 'column_name'"

**Cause**: Column doesn't exist or wrong name
**Solution**: Validate schema before querying:
```python
# Check available columns first
query = f'SELECT * FROM {get_table_name()} LIMIT 1'
df = execute_query(query)
print(df.columns)  # See actual column names
```

### Filter Not Working

**Cause**: Filter SQL not included in WHERE clause
**Solution**: Always build WHERE clause systematically:
```python
where_parts = []
if base_filter := get_base_filter():
    where_parts.append(base_filter)
if user_filter := get_user_filter_clause():
    where_parts.append(user_filter)
where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
```

### Session State Not Persisting

**Cause**: Not initializing before widget creation
**Solution**: Initialize before use:
```python
if 'my_value' not in st.session_state:
    st.session_state.my_value = default_value

widget = st.text_input("Label", value=st.session_state.my_value)
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Keboola Data Apps Guide](https://help.keboola.com/components/data-apps/)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference.html)

## Table Name Helper

```python
def get_table_name():
    """Get fully qualified table name for current context.
    
    Returns:
        Workspace context: '"PROJECT_ID"."BUCKET_ID"."TABLE_NAME"' (quoted, SQL-safe)
        Storage API context: 'BUCKET_ID.TABLE_NAME' (for API endpoints)
    
    Context difference:
    - Workspace uses PROJECT_ID as database name (Snowflake schema)
    - Storage API uses bucket.table format (no project ID)
    """
    mode = get_connection_mode()

    if mode == 'workspace':
        # WORKSPACE CONTEXT: Running in Keboola (has workspace access)
        # Use PROJECT_ID as database qualifier for Snowflake queries
        project_id = os.environ['KBC_PROJECT_ID']  # e.g., "6789"
        bucket = os.environ.get('KBC_BUCKET_ID', 'in.c-analysis')  # e.g., "in.c-main"
        table = os.environ.get('KBC_TABLE_NAME', 'usage_data')  # e.g., "customers"
        
        # Return: "6789"."in.c-main"."customers"
        return f'"{project_id}"."{bucket}"."{table}"'
    else:
        # STORAGE API CONTEXT: Running locally (no workspace)
        # Use bucket.table format for Storage API endpoints
        bucket = 'in.c-analysis'
        table = 'usage_data'
        
        # Return: in.c-analysis.usage_data
        return f'{bucket}.{table}'
```


---

## Metadata

```json
{
  "generated_at": "2025-12-22T14:17:51.318430",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0"
}
```

---

**End of Skill**