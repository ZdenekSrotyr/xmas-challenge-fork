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


## Error Codes Reference

The Storage API returns standard HTTP status codes along with detailed error messages in the response body.

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| **200** | Success | Request completed successfully |
| **201** | Created | Resource created successfully |
| **202** | Accepted | Async job initiated successfully |
| **400** | Bad Request | Invalid parameters, malformed request |
| **401** | Unauthorized | Invalid or missing API token |
| **403** | Forbidden | Valid token but insufficient permissions |
| **404** | Not Found | Table, bucket, or resource doesn't exist |
| **405** | Method Not Allowed | Wrong HTTP method (e.g., GET instead of POST) |
| **422** | Unprocessable Entity | Valid request but business logic error |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server-side error |
| **503** | Service Unavailable | Temporary service disruption |

### Error Response Format

All error responses follow this structure:

```json
{
  "status": "error",
  "error": "Error message",
  "code": "storage.tables.notFound",
  "exceptionId": "unique-error-id",
  "context": {
    "tableId": "in.c-main.customers"
  }
}
```

### Common Error Codes

#### Authentication Errors

**401 - Invalid Token**
```json
{
  "error": "Invalid access token",
  "code": "storage.tokenInvalid"
}
```
**Solution**: Check that `X-StorageApi-Token` header contains valid token.

**403 - Insufficient Permissions**
```json
{
  "error": "You don't have access to this resource",
  "code": "storage.accessDenied"
}
```
**Solution**: Token lacks required permissions. Use token with appropriate scope.

#### Resource Errors

**404 - Table Not Found**
```json
{
  "error": "Table in.c-main.customers not found",
  "code": "storage.tables.notFound"
}
```
**Solution**: Verify table ID format and existence. List tables to confirm.

**404 - Bucket Not Found**
```json
{
  "error": "Bucket in.c-main not found",
  "code": "storage.buckets.notFound"
}
```
**Solution**: Create bucket first or verify bucket ID.

**409 - Resource Already Exists**
```json
{
  "error": "Table in.c-main.customers already exists",
  "code": "storage.tables.alreadyExists"
}
```
**Solution**: Use import endpoint for existing tables, or delete existing table first.

#### Request Errors

**400 - Invalid Parameters**
```json
{
  "error": "Invalid parameter: primaryKey must be an array",
  "code": "storage.validation.invalidInput"
}
```
**Solution**: Check API documentation for correct parameter format.

**400 - Invalid Table ID Format**
```json
{
  "error": "Invalid table ID format",
  "code": "storage.tables.invalidId"
}
```
**Solution**: Use format `stage.c-bucket.table` (e.g., `in.c-main.customers`).

**405 - Method Not Allowed**
```json
{
  "error": "Method not allowed",
  "code": "storage.methodNotAllowed"
}
```
**Solution**: Use POST for `/export-async` and `/import-async` endpoints, not GET.

**422 - Primary Key Required**
```json
{
  "error": "Primary key must be set for incremental loads",
  "code": "storage.tables.primaryKeyRequired"
}
```
**Solution**: Set primary key before using `incremental: "1"` parameter.

**422 - Invalid CSV Data**
```json
{
  "error": "CSV parse error: Invalid row format",
  "code": "storage.tables.invalidCsvData"
}
```
**Solution**: Validate CSV format, check for proper escaping and encoding.

#### Rate Limiting

**429 - Rate Limit Exceeded**
```json
{
  "error": "Rate limit exceeded",
  "code": "storage.rateLimitExceeded",
  "retryAfter": 60
}
```
**Solution**: Implement exponential backoff. Respect `retryAfter` value.

#### Job Errors

**Job Status: error**
```json
{
  "status": "error",
  "error": {
    "message": "Table load failed: Invalid data format",
    "code": "storage.jobs.loadFailed"
  }
}
```
**Solution**: Check job details for specific error. Validate input data.

**Job Status: terminated**
```json
{
  "status": "terminated",
  "error": {
    "message": "Job terminated due to timeout",
    "code": "storage.jobs.timeout"
  }
}
```
**Solution**: Split large operations into smaller chunks.

### Error Handling Best Practices

```python
import requests
import time

def safe_api_call(url, headers, method='get', **kwargs):
    """Make API call with comprehensive error handling."""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            
            # Handle specific status codes
            if response.status_code == 401:
                raise ValueError("Invalid API token. Check KEBOOLA_TOKEN environment variable.")
            
            elif response.status_code == 403:
                raise ValueError("Insufficient permissions. Token lacks required scope.")
            
            elif response.status_code == 404:
                error_data = response.json()
                raise ValueError(f"Resource not found: {error_data.get('error', 'Unknown')}")
            
            elif response.status_code == 405:
                raise ValueError(f"Wrong HTTP method. Endpoint may require POST instead of {method.upper()}.")
            
            elif response.status_code == 422:
                error_data = response.json()
                raise ValueError(f"Request validation failed: {error_data.get('error', 'Unknown')}")
            
            elif response.status_code == 429:
                # Rate limited - retry with backoff
                retry_after = int(response.headers.get('Retry-After', retry_delay * (2 ** attempt)))
                print(f"Rate limited. Retrying after {retry_after}s...")
                time.sleep(retry_after)
                continue
            
            elif response.status_code >= 500:
                # Server error - retry
                if attempt < max_retries - 1:
                    print(f"Server error. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise Exception(f"Server error: {response.status_code}")
            
            # Raise for any other error status
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Request timeout. Retrying...")
                time.sleep(retry_delay)
                continue
            raise TimeoutError("API request timed out after multiple retries")
        
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"Connection error. Retrying...")
                time.sleep(retry_delay)
                continue
            raise ConnectionError("Failed to connect to Keboola API")
    
    raise Exception("Max retries exceeded")

# Usage example
try:
    result = safe_api_call(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token},
        method='post',
        timeout=30
    )
    print(f"Job started: {result['id']}")
except ValueError as e:
    print(f"User error: {e}")
except Exception as e:
    print(f"System error: {e}")
```

### Debugging Errors

**Always check the response body for detailed error information:**

```python
try:
    response = requests.post(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Print full error details
    print(f"Status: {e.response.status_code}")
    print(f"Error body: {e.response.text}")
    
    # Parse error details if JSON
    try:
        error_data = e.response.json()
        print(f"Error code: {error_data.get('code')}")
        print(f"Error message: {error_data.get('error')}")
        print(f"Exception ID: {error_data.get('exceptionId')}")
    except:
        pass
```

**Enable request logging for debugging:**

```python
import logging
import http.client as http_client

# Enable debug logging
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.DEBUG)
```
