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

**Solution**: Implement comprehensive error handling patterns:

### Basic Error Handling

```python
import requests
import time
import logging
from typing import Optional, Dict, Any

def safe_api_call(url: str, headers: Dict[str, str], timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Make API call with proper error handling."""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        logging.error(f"Request timed out after {timeout}s: {url}")
        return None

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error: {e}")
        return None

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        
        if status_code == 401:
            logging.error("Invalid or expired token")
        elif status_code == 403:
            logging.error("Insufficient permissions")
        elif status_code == 404:
            logging.error(f"Resource not found: {url}")
        elif status_code == 429:
            logging.error("Rate limit exceeded")
        elif status_code >= 500:
            logging.error(f"Server error ({status_code})")
        else:
            logging.error(f"HTTP error {status_code}: {e}")
        
        return None

    except ValueError as e:
        logging.error(f"Invalid JSON response: {e}")
        return None

    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return None
```

### Retry Logic with Exponential Backoff

```python
import time
import random
from typing import Optional, Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Optional[Any]:
    """Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd
    
    Returns:
        Function result or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        
        except requests.exceptions.HTTPError as e:
            # Don't retry on client errors (4xx) except rate limiting
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                logging.error(f"Client error {e.response.status_code}, not retrying")
                raise
            
            if attempt == max_retries:
                logging.error(f"Max retries ({max_retries}) exceeded")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent synchronized retries
            if jitter:
                delay = delay * (0.5 + random.random())
            
            logging.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
        
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries:
                logging.error(f"Max retries ({max_retries}) exceeded")
                raise
            
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)
            if jitter:
                delay = delay * (0.5 + random.random())
            
            logging.warning(f"Network error: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
    
    return None

# Usage example
def make_api_call():
    response = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}",
        headers={"X-StorageApi-Token": token},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

result = retry_with_backoff(make_api_call, max_retries=3)
```

### Job Polling with Error Handling

```python
import time
from typing import Dict, Any, Optional

class JobPollingError(Exception):
    """Custom exception for job polling errors."""
    pass

class JobTimeoutError(JobPollingError):
    """Job did not complete within timeout."""
    pass

class JobFailedError(JobPollingError):
    """Job failed with error status."""
    pass

def poll_job_with_error_handling(
    job_id: str,
    timeout: int = 300,
    poll_interval: int = 2,
    max_poll_interval: int = 30
) -> Dict[str, Any]:
    """Poll job status with comprehensive error handling.
    
    Args:
        job_id: Job ID to poll
        timeout: Maximum time to wait (seconds)
        poll_interval: Initial polling interval (seconds)
        max_poll_interval: Maximum polling interval (seconds)
    
    Returns:
        Job details dictionary
    
    Raises:
        JobTimeoutError: If job doesn't complete within timeout
        JobFailedError: If job fails with error status
        requests.HTTPError: If API call fails
    """
    start_time = time.time()
    current_interval = poll_interval
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=30
            )
            response.raise_for_status()
            job = response.json()
            
            status = job.get("status")
            
            # Success case
            if status == "success":
                elapsed = time.time() - start_time
                logging.info(f"Job {job_id} completed successfully in {elapsed:.2f}s")
                return job
            
            # Failure cases
            if status in ["error", "cancelled", "terminated"]:
                error_msg = job.get("error", {}).get("message", "Unknown error")
                error_code = job.get("error", {}).get("code")
                
                raise JobFailedError(
                    f"Job {job_id} failed with status '{status}': {error_msg} "
                    f"(code: {error_code})"
                )
            
            # Still processing
            if status in ["waiting", "processing"]:
                logging.debug(f"Job {job_id} status: {status}")
            else:
                logging.warning(f"Job {job_id} has unexpected status: {status}")
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error polling job {job_id}: {e}. Retrying...")
            # Continue polling despite temporary errors
        
        # Exponential backoff for polling interval
        time.sleep(current_interval)
        current_interval = min(current_interval * 1.5, max_poll_interval)
        current_interval = int(current_interval)
    
    # Timeout reached
    elapsed = time.time() - start_time
    raise JobTimeoutError(
        f"Job {job_id} did not complete within {timeout}s "
        f"(elapsed: {elapsed:.2f}s)"
    )

# Usage example with error handling
try:
    # Start export job
    response = requests.post(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    # Poll with error handling
    job = poll_job_with_error_handling(job_id, timeout=600)
    
    # Download result
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url, timeout=60)
    data_response.raise_for_status()
    
    with open("export.csv", "wb") as f:
        f.write(data_response.content)
    
except JobTimeoutError as e:
    logging.error(f"Job timed out: {e}")
    # Handle timeout: notify user, schedule retry, etc.
    
except JobFailedError as e:
    logging.error(f"Job failed: {e}")
    # Handle failure: check error message, alert, etc.
    
except requests.exceptions.HTTPError as e:
    logging.error(f"API error: {e}")
    # Handle API errors: check token, permissions, etc.
```

### Complete Error Handling Wrapper Class

```python
import requests
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class APIConfig:
    """Configuration for API client."""
    stack_url: str
    token: str
    timeout: int = 30
    max_retries: int = 3
    initial_delay: float = 1.0

class KeboolaAPIClient:
    """Keboola Storage API client with comprehensive error handling."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.base_url = f"https://{config.stack_url}"
        self.headers = {
            "X-StorageApi-Token": config.token,
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        def attempt_request():
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        
        try:
            return retry_with_backoff(
                attempt_request,
                max_retries=self.config.max_retries,
                initial_delay=self.config.initial_delay
            )
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
            raise
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError):
        """Log detailed error information."""
        status_code = error.response.status_code
        
        try:
            error_body = error.response.json()
            error_msg = error_body.get("error", "Unknown error")
            error_code = error_body.get("code")
        except ValueError:
            error_msg = error.response.text
            error_code = None
        
        logging.error(
            f"HTTP {status_code} error: {error_msg} "
            f"(code: {error_code}, url: {error.response.url})"
        )
    
    def get(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """GET request with error handling."""
        response = self._make_request("GET", endpoint, **kwargs)
        return response.json() if response else None
    
    def post(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """POST request with error handling."""
        response = self._make_request("POST", endpoint, **kwargs)
        return response.json() if response else None
    
    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables with error handling."""
        result = self.get("/v2/storage/tables")
        return result if result else []
    
    def export_table(self, table_id: str, output_file: str) -> bool:
        """Export table with complete error handling."""
        try:
            # Start export job
            logging.info(f"Starting export for table {table_id}")
            job_response = self.post(
                f"/v2/storage/tables/{table_id}/export-async"
            )
            
            if not job_response:
                logging.error("Failed to start export job")
                return False
            
            job_id = job_response["id"]
            
            # Poll for completion
            job = poll_job_with_error_handling(job_id, timeout=600)
            
            # Download file
            file_url = job["results"]["file"]["url"]
            logging.info(f"Downloading export from {file_url}")
            
            response = requests.get(file_url, timeout=120)
            response.raise_for_status()
            
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            logging.info(f"Table exported successfully to {output_file}")
            return True
        
        except (JobTimeoutError, JobFailedError) as e:
            logging.error(f"Export job error: {e}")
            return False
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during export: {e}")
            return False
        
        except Exception as e:
            logging.exception(f"Unexpected error during export: {e}")
            return False

# Usage example
config = APIConfig(
    stack_url=os.environ["KEBOOLA_STACK_URL"],
    token=os.environ["KEBOOLA_TOKEN"],
    max_retries=3
)

client = KeboolaAPIClient(config)

# List tables
tables = client.list_tables()
for table in tables:
    print(f"Table: {table['id']}")

# Export table
success = client.export_table("in.c-main.customers", "customers.csv")
if success:
    print("Export completed successfully")
else:
    print("Export failed - check logs for details")
```

### Error Handling Best Practices Summary

**DO**:

- Use specific exception types (`HTTPError`, `Timeout`, `ConnectionError`)
- Implement retry logic with exponential backoff
- Log errors with context (URL, status code, error message)
- Handle rate limiting (429) separately with longer delays
- Set reasonable timeouts (30s for API calls, 120s for downloads)
- Use custom exceptions for domain-specific errors (`JobFailedError`)
- Add jitter to retry delays to prevent thundering herd
- Return `None` or raise exceptions consistently
- Validate responses before processing
- Clean up resources (close files, sessions) in error cases

**DON'T**:

- Retry on client errors (4xx) except rate limiting (429)
- Use bare `except` blocks without logging
- Ignore timeout errors
- Retry indefinitely without max attempts
- Suppress errors silently
- Return different types on success vs error
- Use fixed retry delays (always use backoff)
- Forget to handle network errors (`ConnectionError`)
- Skip validation of JSON responses
- Leave resources open after errors


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
