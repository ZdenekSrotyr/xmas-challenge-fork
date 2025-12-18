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
