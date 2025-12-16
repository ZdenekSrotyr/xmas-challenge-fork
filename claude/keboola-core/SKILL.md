# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/`
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-16T17:00:25.550464

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

**When to Use What**:

```python
# Use WORKSPACE when:
# - Running inside Data App (production)
# - Running transformation
# - Direct SQL queries needed
if 'KBC_PROJECT_ID' in os.environ:
    conn = st.connection('snowflake', type='snowflake')
    query = f'SELECT * FROM "{os.environ["KBC_PROJECT_ID"]}"."{os.environ["in.c-main"]}"."customers"'
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

## Webhooks

Webhooks allow you to receive real-time notifications about events in your Keboola project, such as job completions, errors, and configuration changes.

### Setting Up Webhooks

Webhooks are configured at the project level via the Storage API:

```python
import requests
import os

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

# Create a webhook
response = requests.post(
    f"https://{stack_url}/v2/storage/webhooks",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://your-app.com/webhook",
        "events": [
            "storage.jobSucceeded",
            "storage.jobFailed",
            "storage.tableCreated"
        ],
        "name": "My Webhook"
    }
)
response.raise_for_status()

webhook = response.json()
print(f"Webhook created with ID: {webhook['id']}")
```

### Event Types

Common webhook event types:

**Job Events**:
- `storage.jobSucceeded` - Job completed successfully
- `storage.jobFailed` - Job failed with error
- `storage.jobProcessing` - Job started processing
- `storage.jobWaiting` - Job is queued

**Table Events**:
- `storage.tableCreated` - New table created
- `storage.tableImported` - Data imported to table
- `storage.tableDeleted` - Table deleted

**Configuration Events**:
- `orchestration.jobSucceeded` - Orchestration completed
- `orchestration.jobFailed` - Orchestration failed

### Webhook Payload Format

Webhook requests are POST requests with JSON payload:

```json
{
  "event": "storage.jobSucceeded",
  "data": {
    "id": "12345678",
    "runId": "12345678.87654321",
    "project": {
      "id": "6789",
      "name": "My Project"
    },
    "component": "keboola.ex-db-mysql",
    "configurationId": "123",
    "status": "success",
    "startTime": "2024-01-15T10:30:00+0000",
    "endTime": "2024-01-15T10:35:00+0000",
    "durationSeconds": 300
  },
  "createdTime": "2024-01-15T10:35:01+0000"
}
```

### Webhook Security (Signature Verification)

All webhook requests include an `X-Kbc-Signature` header with HMAC-SHA256 signature for verification:

```python
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_token"  # From webhook creation response

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Get signature from header
    received_signature = request.headers.get('X-Kbc-Signature')
    if not received_signature:
        abort(401, "Missing signature")
    
    # Compute expected signature
    payload = request.get_data()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Verify signature
    if not hmac.compare_digest(received_signature, expected_signature):
        abort(401, "Invalid signature")
    
    # Process webhook
    event_data = request.json
    print(f"Received event: {event_data['event']}")
    
    if event_data['event'] == 'storage.jobFailed':
        # Handle job failure
        job_id = event_data['data']['id']
        send_alert(f"Job {job_id} failed")
    
    return {"status": "ok"}, 200
```

### Managing Webhooks

**List webhooks**:
```python
response = requests.get(
    f"https://{stack_url}/v2/storage/webhooks",
    headers={"X-StorageApi-Token": token}
)
webhooks = response.json()
```

**Update webhook**:
```python
webhook_id = "123"
response = requests.put(
    f"https://{stack_url}/v2/storage/webhooks/{webhook_id}",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://your-app.com/new-webhook",
        "events": ["storage.jobSucceeded"]
    }
)
```

**Delete webhook**:
```python
webhook_id = "123"
response = requests.delete(
    f"https://{stack_url}/v2/storage/webhooks/{webhook_id}",
    headers={"X-StorageApi-Token": token}
)
```

### Best Practices

**DO**:
- Always verify webhook signatures to prevent spoofing
- Use HTTPS endpoints for webhook URLs
- Respond quickly (within 30 seconds) to avoid timeouts
- Process webhooks asynchronously if heavy processing is needed
- Store webhook secrets securely (environment variables, secret managers)
- Log webhook events for debugging
- Handle duplicate events idempotently

**DON'T**:
- Skip signature verification
- Use HTTP (unencrypted) webhook endpoints
- Perform long-running operations in webhook handler
- Hardcode webhook secrets in code
- Assume webhooks arrive in order
- Ignore retry logic for failed deliveries

### Webhook Retries

Keboola automatically retries failed webhook deliveries:
- Retries up to 3 times with exponential backoff
- Considers 2xx status codes as success
- Timeout after 30 seconds per attempt

### Testing Webhooks Locally

Use tunneling tools to test webhooks during development:

```bash
# Using ngrok
ngrok http 5000

# Use the ngrok URL for webhook configuration
# https://abc123.ngrok.io/webhook
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

Many API endpoints that return lists support pagination parameters:

```python
def list_all_tables_paginated():
    """List all tables with pagination support."""
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
```

#### Pagination Parameters

Common pagination parameters across Keboola Storage API:

- **limit**: Number of records to return (default and max vary by endpoint)
- **offset**: Number of records to skip

```python
params = {
    "limit": 100,    # Return up to 100 records
    "offset": 200    # Skip first 200 records
}
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

- **data-preview with pagination**: Quick checks, small datasets (<1000 rows)
- **List endpoints with pagination**: Browsing tables, buckets, configurations
- **Async export**: Production data export, large tables (>1000 rows)

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
        response.raise_for_status()

        job = response.json()

        if job["status"] == "success":
            return job
        elif job["status"] in ["error", "cancelled", "terminated"]:
            error_msg = job.get("error", {}).get("message", "Unknown error")
            raise Exception(f"Job failed with status {job['status']}: {error_msg}")

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

```python
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
- [Keboola Data Apps Guide](https://developers.keboola.com/extend/data-apps/)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference.html)

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


---

## Metadata

```json
{
  "generated_at": "2025-12-16T17:00:25.550464",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0"
}
```

---

**End of Skill**