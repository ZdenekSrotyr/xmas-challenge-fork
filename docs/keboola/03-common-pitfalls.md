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

**Solution**: Implement comprehensive error handling with retries and structured responses:

```python
import time
import logging
from typing import Optional, Dict, Any
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

class KeboolaAPIError(Exception):
    """Base exception for Keboola API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class KeboolaAuthError(KeboolaAPIError):
    """Authentication failed (401)."""
    pass

class KeboolaNotFoundError(KeboolaAPIError):
    """Resource not found (404)."""
    pass

class KeboolaRateLimitError(KeboolaAPIError):
    """Rate limit exceeded (429)."""
    pass

class KeboolaValidationError(KeboolaAPIError):
    """Invalid request data (400, 422)."""
    pass

def parse_error_response(response) -> str:
    """Extract error message from Keboola API response."""
    try:
        error_data = response.json()
        # Keboola API error format
        if 'error' in error_data:
            return error_data['error']
        if 'message' in error_data:
            return error_data['message']
        return str(error_data)
    except Exception:
        return response.text or f"HTTP {response.status_code}"

def api_call_with_retry(
    url: str,
    headers: Dict[str, str],
    method: str = 'GET',
    max_retries: int = 3,
    timeout: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """Make API call with exponential backoff retry logic.
    
    Args:
        url: API endpoint URL
        headers: Request headers (must include X-StorageApi-Token)
        method: HTTP method (GET, POST, etc.)
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests
    
    Returns:
        Parsed JSON response
    
    Raises:
        KeboolaAuthError: Authentication failed
        KeboolaNotFoundError: Resource not found
        KeboolaRateLimitError: Rate limit exceeded after retries
        KeboolaValidationError: Invalid request data
        KeboolaAPIError: Other API errors
    """
    import requests
    
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except Timeout:
            logging.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise KeboolaAPIError(
                    f"Request timed out after {max_retries} attempts",
                    response=None
                )
            time.sleep(2 ** attempt)

        except ConnectionError as e:
            logging.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise KeboolaAPIError(
                    f"Connection failed after {max_retries} attempts: {str(e)}",
                    response=None
                )
            time.sleep(2 ** attempt)

        except HTTPError as e:
            error_msg = parse_error_response(e.response)
            status_code = e.response.status_code

            # Don't retry client errors (except rate limit)
            if status_code == 401:
                raise KeboolaAuthError(
                    f"Authentication failed: {error_msg}",
                    status_code=status_code,
                    response=e.response.json() if e.response.content else None
                )
            
            elif status_code == 404:
                raise KeboolaNotFoundError(
                    f"Resource not found: {error_msg}",
                    status_code=status_code,
                    response=e.response.json() if e.response.content else None
                )
            
            elif status_code in [400, 422]:
                raise KeboolaValidationError(
                    f"Invalid request: {error_msg}",
                    status_code=status_code,
                    response=e.response.json() if e.response.content else None
                )
            
            elif status_code == 429:
                # Rate limited - retry with exponential backoff
                wait_time = 2 ** attempt
                logging.warning(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise KeboolaRateLimitError(
                        f"Rate limit exceeded after {max_retries} attempts",
                        status_code=status_code,
                        response=e.response.json() if e.response.content else None
                    )
                time.sleep(wait_time)
            
            elif status_code >= 500:
                # Server error - retry
                wait_time = 2 ** attempt
                logging.warning(f"Server error {status_code}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise KeboolaAPIError(
                        f"Server error after {max_retries} attempts: {error_msg}",
                        status_code=status_code,
                        response=e.response.json() if e.response.content else None
                    )
                time.sleep(wait_time)
            
            else:
                # Other HTTP errors - don't retry
                raise KeboolaAPIError(
                    f"HTTP {status_code}: {error_msg}",
                    status_code=status_code,
                    response=e.response.json() if e.response.content else None
                )

        except RequestException as e:
            logging.error(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise KeboolaAPIError(
                    f"Request failed after {max_retries} attempts: {str(e)}",
                    response=None
                )
            time.sleep(2 ** attempt)

    raise KeboolaAPIError("Max retries exceeded", response=None)

# Usage examples
def get_table_info(table_id: str) -> Dict[str, Any]:
    """Get table information with error handling."""
    try:
        return api_call_with_retry(
            url=f"https://{stack_url}/v2/storage/tables/{table_id}",
            headers={"X-StorageApi-Token": token},
            method='GET',
            max_retries=3,
            timeout=30
        )
    except KeboolaNotFoundError:
        logging.error(f"Table {table_id} does not exist")
        raise
    except KeboolaAuthError:
        logging.error("Invalid or expired token")
        raise
    except KeboolaAPIError as e:
        logging.error(f"Failed to get table info: {e.message}")
        raise

def export_table_with_error_handling(table_id: str) -> str:
    """Export table with comprehensive error handling."""
    try:
        # Start export job
        job_response = api_call_with_retry(
            url=f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
            headers={"X-StorageApi-Token": token},
            method='POST',
            max_retries=3,
            timeout=30
        )
        job_id = job_response["id"]
        
        # Poll for completion
        timeout = 300
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                job = api_call_with_retry(
                    url=f"https://{stack_url}/v2/storage/jobs/{job_id}",
                    headers={"X-StorageApi-Token": token},
                    method='GET',
                    max_retries=2,  # Fewer retries for polling
                    timeout=15
                )
                
                if job["status"] == "success":
                    file_url = job["results"]["file"]["url"]
                    return file_url
                
                elif job["status"] in ["error", "cancelled", "terminated"]:
                    error_msg = job.get("error", {}).get("message", "Unknown error")
                    raise KeboolaAPIError(
                        f"Export job failed: {error_msg}",
                        response=job
                    )
                
                time.sleep(2)
            
            except KeboolaAPIError as e:
                # If job status check fails, re-raise
                logging.error(f"Failed to check job status: {e.message}")
                raise
        
        raise KeboolaAPIError(f"Export job {job_id} timed out after {timeout}s")
    
    except KeboolaNotFoundError:
        logging.error(f"Table {table_id} not found")
        raise
    except KeboolaAuthError:
        logging.error("Authentication failed - check your token")
        raise
    except KeboolaValidationError as e:
        logging.error(f"Invalid export request: {e.message}")
        raise
    except KeboolaAPIError as e:
        logging.error(f"Export failed: {e.message}")
        raise
```

**Error Handling Best Practices**:

1. **Use custom exceptions** for different error types
2. **Retry transient errors** (timeouts, rate limits, 5xx)
3. **Don't retry client errors** (401, 404, 400)
4. **Parse error responses** to get meaningful messages
5. **Log errors** with appropriate severity
6. **Set timeouts** on all requests
7. **Implement exponential backoff** for retries
8. **Handle job polling errors** separately from API errors


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
