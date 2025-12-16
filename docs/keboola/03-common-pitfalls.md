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

        job = response.json()

        if job["status"] == "success":
            return job
        elif job["status"] == "error":
            raise Exception(f"Job failed: {job.get('error', {}).get('message')}")

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

## 6. Using Wrong Tool for the Job

**Problem**: Using Storage API for simple validation or MCP for production pipelines

**Solution**: Choose the right tool:

```python
# ❌ WRONG - Using API for simple schema check
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}",
    headers={"X-StorageApi-Token": token}
)
columns = [col["name"] for col in response.json()["columns"]]

# ✅ CORRECT - Use MCP for quick validation
mcp__keboola__get_table(table_id)
# → Immediately see all columns and types

# ❌ WRONG - Using MCP in production pipeline
def daily_etl():
    data = mcp__keboola__query_data(sql_query="SELECT * FROM large_table")
    # MCP not designed for production/automation

# ✅ CORRECT - Use Storage API for production
def daily_etl():
    response = requests.get(
        f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
        headers={"X-StorageApi-Token": token}
    )
    job_id = response.json()["id"]
    result = wait_for_job(job_id)
    # Reliable, async, handles large datasets
```

**Quick Guide**:
- **Development/Validation** → Use MCP Server
- **Production/Automation** → Use Storage API
- **See**: [MCP Server vs Direct API Usage](04-mcp-vs-api.md)
