# Core Concepts

## Overview

Keboola is a cloud-based data platform that enables you to extract, transform, and load data from various sources. The platform provides a complete suite of tools for building data pipelines, from initial data ingestion to final analytics and reporting.

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
