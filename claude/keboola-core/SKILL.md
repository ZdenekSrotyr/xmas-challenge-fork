# Keboola Platform Knowledge for Claude Code

> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.
> Source: `docs/keboola/`
> Generator: `scripts/generators/claude_generator.py`
> Generated: 2025-12-16T09:47:57.473968

---

## Overview

This skill provides comprehensive knowledge about the Keboola platform,
including API usage, best practices, and common pitfalls.

**When to activate this skill:**
- User asks about Keboola Storage API
- User needs help with Keboola Jobs API
- User wants to run transformations or components programmatically
- User needs to monitor job execution or handle job errors
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
# Get table export URL
response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token}
)

job_id = response.json()["id"]

# Poll for completion
import time
while True:
    job_response = requests.get(
        f"https://{stack_url}/v2/storage/jobs/{job_id}",
        headers={"X-StorageApi-Token": token}
    )

    job = job_response.json()
    if job["status"] in ["success", "error"]:
        break

    time.sleep(2)

# Download data
if job["status"] == "success":
    file_url = job["results"]["file"]["url"]
    data_response = requests.get(file_url)

    import csv
    import io

    reader = csv.DictReader(io.StringIO(data_response.text))
    data = list(reader)
```

## Writing Tables

### Create Table from CSV

```python
# Upload CSV file
csv_data = "id,name,value\n1,foo,100\n2,bar,200"

response = requests.post(
    f"https://{stack_url}/v2/storage/buckets/in.c-main/tables-async",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "text/csv"
    },
    params={
        "name": "my_table",
        "dataString": csv_data
    }
)

job_id = response.json()["id"]
# Poll job until completion (same as above)
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

### Incremental Loads

Use changed_since parameter for incremental updates:

```python
from datetime import datetime, timedelta

# Get data changed in last 24 hours
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

response = requests.get(
    f"https://{stack_url}/v2/storage/tables/{table_id}/export-async",
    headers={"X-StorageApi-Token": token},
    params={"changedSince": yesterday}
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


---

## Metadata

```json
{
  "generated_at": "2025-12-16T09:47:57.473968",
  "source_path": "docs/keboola",
  "generator": "claude_generator.py v1.0"
}
```

---

**End of Skill**

---

<!-- Source: 02b-jobs-api.md -->

# Jobs API

## Overview

The Jobs API allows you to run and monitor asynchronous operations in Keboola, including:
- Transformations (SQL, Python, R, Julia)
- Component configurations (extractors, writers)
- Data exports and imports

All Jobs API operations follow the same pattern: create a job, poll for status, retrieve results.

## Running Transformations

### Trigger a Transformation

```python
import requests
import os

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

# Run a transformation by its configuration ID
config_id = "1234567"  # Your transformation config ID

response = requests.post(
    f"https://{stack_url}/v2/storage/jobs",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "component": "keboola.snowflake-transformation",
        "mode": "run",
        "config": config_id
    }
)

job = response.json()
job_id = job["id"]
print(f"Transformation started: Job ID {job_id}")
```

### Monitor Job Status

```python
import time

def wait_for_job(job_id, timeout=600, poll_interval=5):
    """
    Wait for a job to complete.
    
    Args:
        job_id: The job ID to monitor
        timeout: Maximum time to wait in seconds (default: 10 minutes)
        poll_interval: Time between status checks in seconds
    
    Returns:
        dict: Final job details
    
    Raises:
        TimeoutError: If job doesn't complete within timeout
        Exception: If job fails
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        
        job = response.json()
        status = job["status"]
        
        print(f"Job {job_id}: {status}")
        
        if status == "success":
            print(f"Job completed successfully in {time.time() - start_time:.1f}s")
            return job
        elif status == "error":
            error_msg = job.get("result", {}).get("message", "Unknown error")
            raise Exception(f"Job {job_id} failed: {error_msg}")
        elif status in ["cancelled", "terminated"]:
            raise Exception(f"Job {job_id} was {status}")
        
        # Job still running
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

# Usage
try:
    result = wait_for_job(job_id)
    print("Transformation completed successfully")
except Exception as e:
    print(f"Error: {e}")
```

## Running Other Components

### Run an Extractor Configuration

```python
# Run a data extractor
response = requests.post(
    f"https://{stack_url}/v2/storage/jobs",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "component": "keboola.ex-db-mysql",  # Component ID
        "mode": "run",
        "config": "987654"  # Configuration ID
    }
)

job_id = response.json()["id"]
wait_for_job(job_id)
```

### Run with Custom Parameters

```python
# Override configuration parameters at runtime
response = requests.post(
    f"https://{stack_url}/v2/storage/jobs",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "component": "keboola.snowflake-transformation",
        "mode": "run",
        "config": config_id,
        "configData": {
            "parameters": {
                "incremental": True,
                "days_back": 7
            }
        }
    }
)
```

## Job Status and Results

### Understanding Job Status

Possible job statuses:
- **waiting**: Job queued, not yet started
- **processing**: Job is currently running
- **success**: Job completed successfully
- **error**: Job failed (check error details)
- **cancelled**: Job was manually cancelled
- **terminated**: Job was terminated (usually due to timeout)
- **terminating**: Job is being terminated

### Retrieve Job Results

```python
# Get detailed job information
response = requests.get(
    f"https://{stack_url}/v2/storage/jobs/{job_id}",
    headers={"X-StorageApi-Token": token}
)

job = response.json()

# Check execution details
print(f"Status: {job['status']}")
print(f"Started: {job.get('startTime')}")
print(f"Ended: {job.get('endTime')}")
print(f"Duration: {job.get('durationSeconds')}s")

# For failed jobs, get error details
if job["status"] == "error":
    error = job.get("result", {})
    print(f"Error message: {error.get('message')}")
    print(f"Error type: {error.get('exceptionId')}")
    
    # Some jobs include detailed logs
    if "logs" in job:
        print(f"Logs: {job['logs']}")
```

## Common Patterns

### Run Multiple Jobs in Sequence

```python
def run_job_sequence(jobs_config):
    """
    Run multiple jobs in sequence.
    
    Args:
        jobs_config: List of job configurations
        
    Returns:
        list: Results from all jobs
    """
    results = []
    
    for i, config in enumerate(jobs_config, 1):
        print(f"Running job {i}/{len(jobs_config)}: {config['component']}")
        
        response = requests.post(
            f"https://{stack_url}/v2/storage/jobs",
            headers={
                "X-StorageApi-Token": token,
                "Content-Type": "application/json"
            },
            json=config
        )
        
        job_id = response.json()["id"]
        
        try:
            result = wait_for_job(job_id)
            results.append(result)
        except Exception as e:
            print(f"Job {i} failed: {e}")
            raise  # Stop sequence on first failure
    
    return results

# Usage
jobs = [
    {
        "component": "keboola.ex-db-mysql",
        "mode": "run",
        "config": "123"
    },
    {
        "component": "keboola.snowflake-transformation",
        "mode": "run",
        "config": "456"
    }
]

run_job_sequence(jobs)
```

### Run Jobs in Parallel

```python
import concurrent.futures

def run_single_job(job_config):
    """Run a single job and wait for completion."""
    response = requests.post(
        f"https://{stack_url}/v2/storage/jobs",
        headers={
            "X-StorageApi-Token": token,
            "Content-Type": "application/json"
        },
        json=job_config
    )
    
    job_id = response.json()["id"]
    return wait_for_job(job_id)

def run_jobs_parallel(jobs_config, max_workers=3):
    """
    Run multiple jobs in parallel.
    
    Args:
        jobs_config: List of job configurations
        max_workers: Maximum number of parallel jobs
        
    Returns:
        list: Results from all jobs
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_job, config) for config in jobs_config]
        results = []
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Job failed: {e}")
                # Continue processing other jobs
        
        return results

# Usage: Run multiple extractors in parallel
jobs = [
    {"component": "keboola.ex-db-mysql", "mode": "run", "config": "123"},
    {"component": "keboola.ex-google-analytics", "mode": "run", "config": "456"},
    {"component": "keboola.ex-salesforce", "mode": "run", "config": "789"}
]

run_jobs_parallel(jobs, max_workers=3)
```

### List Recent Jobs

```python
# Get list of recent jobs
response = requests.get(
    f"https://{stack_url}/v2/storage/jobs",
    headers={"X-StorageApi-Token": token},
    params={
        "limit": 50,  # Number of jobs to retrieve
        "offset": 0   # Pagination offset
    }
)

jobs = response.json()

for job in jobs:
    print(f"{job['id']}: {job['component']} - {job['status']}")
```

## Component IDs Reference

Common component IDs for Jobs API:

**Transformations**:
- `keboola.snowflake-transformation` - Snowflake SQL
- `keboola.python-transformation-v2` - Python
- `keboola.r-transformation` - R
- `transformation` - Legacy transformations

**Extractors**:
- `keboola.ex-db-mysql` - MySQL
- `keboola.ex-db-postgresql` - PostgreSQL
- `keboola.ex-google-analytics` - Google Analytics
- `keboola.ex-salesforce` - Salesforce

**Writers**:
- `keboola.wr-db-mysql` - MySQL
- `keboola.wr-google-bigquery-v2` - BigQuery
- `keboola.wr-snowflake` - Snowflake

To find component IDs in your project, list components:
```python
response = requests.get(
    f"https://{stack_url}/v2/storage/components",
    headers={"X-StorageApi-Token": token}
)
```


## 6. Not Handling Job Timeouts

**Problem**: Transformation jobs timing out without proper error handling

**Solution**: Set appropriate timeouts and handle gracefully:

```python
def wait_for_job_with_timeout(job_id, timeout=600):
    """
    Wait for job with proper timeout handling.
    
    Different job types have different expected durations:
    - Simple transformations: 30-60s
    - Large data extracts: 5-10 minutes
    - Complex workflows: 10-30 minutes
    """
    start_time = time.time()
    poll_interval = 5
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"https://{stack_url}/v2/storage/jobs/{job_id}",
                headers={"X-StorageApi-Token": token},
                timeout=30  # Request timeout
            )
            response.raise_for_status()
            
            job = response.json()
            
            if job["status"] in ["success", "error", "cancelled", "terminated"]:
                return job
            
            time.sleep(poll_interval)
            
        except requests.exceptions.Timeout:
            print(f"Status check timed out, retrying...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error checking job status: {e}")
            time.sleep(poll_interval)
    
    # Timeout reached - try to get final status
    try:
        response = requests.get(
            f"https://{stack_url}/v2/storage/jobs/{job_id}",
            headers={"X-StorageApi-Token": token}
        )
        job = response.json()
        raise TimeoutError(
            f"Job {job_id} did not complete in {timeout}s. "
            f"Current status: {job.get('status')}. "
            f"Consider increasing timeout or checking job configuration."
        )
    except requests.exceptions.RequestException:
        raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")
```

## 7. Using Wrong Component IDs

**Problem**: Job creation fails with "Component not found" error

**Solution**: Verify component ID before running:

```python
def get_component_configurations(component_id):
    """List all configurations for a component."""
    response = requests.get(
        f"https://{stack_url}/v2/storage/components/{component_id}/configs",
        headers={"X-StorageApi-Token": token}
    )
    
    if response.status_code == 404:
        print(f"Component '{component_id}' not found in this project")
        return None
    
    response.raise_for_status()
    return response.json()

# Validate before running
component_id = "keboola.snowflake-transformation"
config_id = "123456"

configs = get_component_configurations(component_id)
if configs:
    config_exists = any(c["id"] == config_id for c in configs)
    if config_exists:
        # Safe to run
        run_job(component_id, config_id)
    else:
        print(f"Config {config_id} not found for component {component_id}")
```
