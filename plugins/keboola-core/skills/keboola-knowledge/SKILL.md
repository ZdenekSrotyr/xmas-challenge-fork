---
name: keboola-knowledge
description: Expert knowledge of the Keboola platform covering workspace management, Storage API, Jobs API, component deployment, and orchestration. Activates when users ask about Keboola concepts, APIs, data operations, component development, or when business requirements need translation to Keboola operations.
allowed-tools: ['*']
---

# Keboola Platform Knowledge Skill

You are an expert on the Keboola data platform. Your goal is to help users understand and work with Keboola effectively, whether they're business users translating requirements into operations or developers building custom components and integrations.

## When to Use This Skill

This skill activates when users mention or ask about:

- Keboola platform concepts (workspace, branch, configuration, stack URL, etc.)
- Storage API operations (reading/writing tables, buckets, metadata)
- Jobs API operations (running transformations, components, orchestrations)
- Regional deployment and stack URL questions
- API endpoint and authentication troubleshooting
- Component development and deployment
- Flows and orchestration
- MCP server integration
- Data pipeline architecture in Keboola
- Workspace ID confusion or hierarchy questions
- Input/Output mapping patterns
- Best practices for Keboola operations

## Core Concepts: The Keboola Hierarchy

### Workspace → Branch → Config Model

Keboola uses a three-level hierarchy for organizing data and operations:

```
Organization
  └─ Project (aka Workspace)
      ├─ Main Branch (default branch)
      │   ├─ Storage (Tables & Buckets)
      │   ├─ Configurations (Component configs)
      │   └─ Orchestrations/Flows
      └─ Development Branches
          ├─ Storage (isolated copy)
          ├─ Configurations (branch-specific)
          └─ Orchestrations/Flows
```

#### Key Concepts:

**Project (Workspace)**
- The top-level container for your data and operations
- Has a unique Project ID (e.g., `12345`)
- Contains storage, configurations, and orchestrations
- Each project has its own API token for authentication

**Branch**
- Isolated environment within a project
- Default branch: "Main" (branch ID: `default`)
- Development branches: For testing changes safely
- Each branch has its own storage space and configurations

**Configuration**
- Specific setup of a component (extractor, writer, transformation, etc.)
- Has a unique Configuration ID
- Stores parameters, input/output mappings, and runtime settings
- Can be versioned and rolled back

**Workspace (Context-Dependent Term)**
⚠️ **IMPORTANT**: "Workspace" has TWO meanings in Keboola:

1. **Project Workspace** = The entire project (what most people mean)
2. **Transformation Workspace** = A database environment for SQL transformations

When users say "workspace ID," they usually mean **Project ID**.

<details>
<summary>Deep Dive: Understanding the Workspace ID Confusion</summary>

**The Confusion:**

Users often see different IDs and get confused about which one to use:

- **Project ID**: `12345` (numeric, identifies your project)
- **Storage Backend ID**: `KBC_USE4_361` (string, internal database identifier)
- **Workspace Database Name**: `KEBOOLA_12345` (transformation workspace)

**Which ID to Use Where:**

| Use Case | ID Type | Example |
|----------|---------|---------|
| API calls (Storage, Jobs) | Project ID | `12345` |
| MCP server authentication | Project ID | `12345` |
| SQL queries (fully qualified names) | Storage Backend ID | `KBC_USE4_361` |
| Transformation workspace connections | Workspace DB Name | `KEBOOLA_12345` |

**How to Find Your Project ID:**

1. Look at the URL when logged into Keboola: `https://connection.keboola.com/admin/projects/12345/...`
2. Use MCP: `mcp__keboola__get_project_info` returns the project ID
3. Check Storage API: `GET /v2/storage` returns project metadata

</details>

### Storage Structure

Storage organizes data in a bucket → table hierarchy:

```
Storage
  ├─ in.c-{bucket-name}      (Input buckets)
  │   └─ table-name           (Tables with columns & rows)
  ├─ out.c-{bucket-name}      (Output buckets)
  │   └─ table-name
  └─ sys.c-{bucket-name}      (System buckets)
      └─ table-name
```

**Bucket Types:**
- `in.c-*` - Input data (from extractors)
- `out.c-*` - Output data (from transformations)
- `sys.c-*` - System data (logs, metadata)

**Table Identification:**
- **Table ID**: `out.c-analysis.usage_data` (used in API calls)
- **Fully Qualified Name**: `"KBC_USE4_361"."out.c-analysis"."usage_data"` (used in SQL)

## Storage API Patterns

The Storage API is the primary interface for reading and writing data in Keboola.

### Reading Tables

**Using MCP Server (Recommended):**

```python
# Get table schema and metadata
mcp__keboola__get_table(table_id="out.c-analysis.sales_data")

# Returns:
# {
#   "id": "out.c-analysis.sales_data",
#   "name": "sales_data",
#   "bucket_id": "out.c-analysis",
#   "columns": ["date", "product", "revenue", "quantity"],
#   "primary_key": ["date", "product"],
#   "row_count": 15234,
#   "data_size_bytes": 524288,
#   "database_native_types": {
#     "date": "DATE",
#     "product": "VARCHAR(255)",
#     "revenue": "DECIMAL(10,2)",
#     "quantity": "INTEGER"
#   }
# }

# Query data directly
mcp__keboola__query_data(
    sql='SELECT "product", SUM("revenue") as total FROM "KBC_USE4_361"."out.c-analysis"."sales_data" GROUP BY "product"',
    query_name="Product Revenue Summary"
)
```

**Using Storage API Directly:**

```python
import requests
import os

# Configuration
# IMPORTANT: Use YOUR stack URL, not hardcoded connection.keboola.com
stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
project_id = 12345
storage_token = os.environ["KEBOOLA_TOKEN"]
base_url = f"https://{stack_url}"

headers = {
    "X-StorageApi-Token": storage_token,
    "Content-Type": "application/json"
}

# List tables in a bucket
response = requests.get(
    f"{base_url}/v2/storage/buckets/out.c-analysis/tables",
    headers=headers
)
tables = response.json()

# Get table detail
response = requests.get(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data",
    headers=headers
)
table_detail = response.json()

# Export table data (async)
response = requests.post(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data/export-async",
    headers=headers,
    json={"format": "json"}  # or "csv"
)
job_id = response.json()["id"]

# Check export job status
job_response = requests.get(
    f"{base_url}/v2/storage/jobs/{job_id}",
    headers=headers
)
# When status == "success", get file from job_response["results"]["file"]["url"]
```

### Writing Tables

**Create or Replace Table:**

```python
import csv
import requests

# Prepare CSV data
csv_file = "/tmp/data.csv"
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["product", "revenue", "quantity"])
    writer.writerow(["Widget", "1500.50", "25"])
    writer.writerow(["Gadget", "2300.75", "42"])

# Upload to Storage
with open(csv_file, 'rb') as f:
    response = requests.post(
        f"{base_url}/v2/storage/buckets/out.c-analysis/tables-async",
        headers=headers,
        data={
            "name": "sales_data",
            "dataFile": f,
            "primaryKey[]": ["product"],  # Optional
            "delimiter": ",",
            "enclosure": '"'
        }
    )

job_id = response.json()["id"]
# Poll job status until complete
```

**Incremental Load:**

```python
# Append data to existing table
response = requests.post(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data/import-async",
    headers=headers,
    data={
        "dataFile": open("/tmp/new_data.csv", 'rb'),
        "incremental": 1,  # Append mode
        "delimiter": ",",
        "enclosure": '"'
    }
)
```

**Update Specific Rows (Upsert):**

```python
# Requires primary key on table
response = requests.post(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data/import-async",
    headers=headers,
    data={
        "dataFile": open("/tmp/updates.csv", 'rb'),
        "incremental": 1,
        "primaryKey[]": ["product"],  # Must match table's primary key
        "delimiter": ",",
        "enclosure": '"'
    }
)
# Rows with matching primary key are updated, new rows are inserted
```

<details>
<summary>Deep Dive: Table Metadata and Attributes</summary>

**Table Metadata:**

Keboola tables can have metadata attached for documentation and automation:

```python
# Add metadata to table
requests.post(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data/metadata",
    headers=headers,
    json={
        "key": "description",
        "value": "Daily sales data aggregated by product",
        "provider": "my-component"
    }
)

# Add column metadata
requests.post(
    f"{base_url}/v2/storage/tables/out.c-analysis.sales_data/columns/revenue/metadata",
    headers=headers,
    json={
        "key": "data_type",
        "value": "currency_usd",
        "provider": "my-component"
    }
)
```

**Column Types:**

Keboola automatically detects column types, but you can specify them explicitly:

```python
# When creating table
response = requests.post(
    f"{base_url}/v2/storage/buckets/out.c-analysis/tables-async",
    headers=headers,
    json={
        "name": "sales_data",
        "dataFile": file_upload,
        "columns": ["product", "revenue", "quantity"],
        "columnMetadata": {
            "product": [{"key": "KBC.datatype.type", "value": "VARCHAR"}],
            "revenue": [{"key": "KBC.datatype.type", "value": "DECIMAL"}],
            "quantity": [{"key": "KBC.datatype.type", "value": "INTEGER"}]
        }
    }
)
```

</details>

## Jobs API Patterns

The Jobs API allows you to trigger and monitor component executions, transformations, and orchestrations.

### Running Components

**Run a Configuration:**

```python
# Run a specific component configuration
# Note: base_url should be https://{your-stack-url} as shown in Storage API section
response = requests.post(
    f"{base_url}/v2/storage/components/keboola.ex-db-mysql/configs/123456/run",
    headers=headers,
    json={
        "config": "123456",
        "tag": "production"  # Optional: use specific config version
    }
)

job_id = response.json()["id"]
print(f"Job started: {job_id}")
```

**Monitor Job Status:**

```python
import time

def wait_for_job(job_id, timeout=300):
    """Wait for job to complete, poll every 5 seconds."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(
            f"{base_url}/v2/storage/jobs/{job_id}",
            headers=headers
        )
        job = response.json()

        status = job["status"]

        if status == "success":
            print(f"Job {job_id} completed successfully!")
            return job
        elif status in ["error", "cancelled", "terminated"]:
            print(f"Job {job_id} failed with status: {status}")
            print(f"Error: {job.get('error', {}).get('message', 'Unknown error')}")
            raise Exception(f"Job failed: {status}")

        print(f"Job {job_id} status: {status}")
        time.sleep(5)

    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

# Usage
job_result = wait_for_job(job_id)
```

**Run with Custom Parameters:**

```python
# Override config parameters at runtime
response = requests.post(
    f"{base_url}/v2/storage/components/keboola.ex-db-mysql/configs/123456/run",
    headers=headers,
    json={
        "config": "123456",
        "configData": {
            "parameters": {
                "db": {
                    "host": "custom-host.example.com",
                    "port": 3306
                }
            }
        }
    }
)
```

### Running Transformations

**Snowflake Transformation:**

```python
response = requests.post(
    f"{base_url}/v2/storage/components/keboola.snowflake-transformation/configs/123456/run",
    headers=headers
)
```

**Python Transformation:**

```python
response = requests.post(
    f"{base_url}/v2/storage/components/keboola.python-transformation-v2/configs/123456/run",
    headers=headers
)
```

<details>
<summary>Deep Dive: Job Lifecycle and Error Handling</summary>

**Job Statuses:**

| Status | Description |
|--------|-------------|
| `created` | Job created, waiting to start |
| `waiting` | Queued, waiting for resources |
| `processing` | Currently running |
| `success` | Completed successfully |
| `error` | Failed with error |
| `cancelled` | User cancelled |
| `terminated` | System terminated (timeout, resource limit) |

**Error Handling Pattern:**

```python
def run_component_safely(component_id, config_id, max_retries=3):
    """Run component with retries and error handling."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{base_url}/v2/storage/components/{component_id}/configs/{config_id}/run",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            job_id = response.json()["id"]
            job_result = wait_for_job(job_id)

            return job_result

        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1}: Request timed out")
            if attempt == max_retries - 1:
                raise
            time.sleep(10)

        except Exception as e:
            print(f"Attempt {attempt + 1}: Error - {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(10)
```

**Getting Job Logs:**

```python
# Get job events (detailed logs)
response = requests.get(
    f"{base_url}/v2/storage/jobs/{job_id}/events",
    headers=headers
)
events = response.json()

for event in events:
    print(f"[{event['created']}] {event['message']}")
```

</details>

## Custom Python Component Deployment

### Component Structure

A Keboola Python component follows this structure:

```
my-component/
├── src/
│   ├── component.py          # Main component logic
│   └── component.json        # Component definition
├── tests/
│   └── test_component.py     # Unit tests
├── Dockerfile                # Container definition
├── deploy.sh                 # Deployment script
└── requirements.txt          # Python dependencies
```

### Basic Component Template

**component.py:**

```python
#!/usr/bin/env python3
import csv
import os
import sys
from keboola.component import CommonInterface

# Initialize component interface
ci = CommonInterface()

# Get parameters from configuration
params = ci.configuration.parameters
db_host = params.get('db', {}).get('host')
db_port = params.get('db', {}).get('port', 3306)

# Get input tables
input_tables = ci.get_input_tables_definitions()

# Process data
try:
    for table in input_tables:
        input_file = table.full_path
        output_file = f"{ci.tables_out_path}/processed_{table.name}.csv"

        # Read input
        with open(input_file, 'r') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)

        # Process (example: add calculated column)
        for row in rows:
            row['calculated_value'] = float(row['value']) * 2

        # Write output
        with open(output_file, 'w', newline='') as outfile:
            if rows:
                writer = csv.DictWriter(outfile, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        # Create output manifest
        ci.write_table_manifest(
            file_name=f"processed_{table.name}.csv",
            destination=f"out.c-my-component.processed_{table.name}",
            primary_key=['id'],
            incremental=False
        )

    print("Component completed successfully!")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

**component.json:**

```json
{
  "name": "my-component",
  "type": "extractor",
  "version": "1.0.0",
  "description": "My custom Keboola component",
  "data": {
    "definition": {
      "type": "dockerhub",
      "uri": "my-dockerhub-username/my-component"
    },
    "configuration_schema": {
      "type": "object",
      "properties": {
        "db": {
          "type": "object",
          "properties": {
            "host": {
              "type": "string",
              "title": "Database Host"
            },
            "port": {
              "type": "integer",
              "title": "Database Port",
              "default": 3306
            }
          },
          "required": ["host"]
        }
      }
    },
    "vendor": {
      "contact": ["support@example.com"]
    }
  }
}
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY src/ /code/

# Set entrypoint
ENTRYPOINT ["python", "-u", "/code/component.py"]
```

**requirements.txt:**

```
keboola.component==1.6.0
```

### Deployment Process

**1. Build and Push Docker Image:**

```bash
# Build image
docker build -t my-dockerhub-username/my-component:1.0.0 .

# Test locally
docker run --rm \
  -v $(pwd)/data:/data \
  my-dockerhub-username/my-component:1.0.0

# Push to Docker Hub
docker push my-dockerhub-username/my-component:1.0.0
```

**2. Register Component in Keboola:**

```bash
# Use Keboola Developer Portal or CLI
# https://components.keboola.com/

# Or use API
curl -X POST "https://connection.keboola.com/v2/storage/dev-branches/components" \
  -H "X-StorageApi-Token: ${STORAGE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @component.json
```

**3. Create Configuration:**

```bash
# Via API
curl -X POST "https://connection.keboola.com/v2/storage/components/my-vendor.my-component/configs" \
  -H "X-StorageApi-Token: ${STORAGE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Config",
    "description": "Main production configuration",
    "configuration": {
      "parameters": {
        "db": {
          "host": "prod-db.example.com",
          "port": 3306
        }
      },
      "storage": {
        "input": {
          "tables": [
            {
              "source": "in.c-data.raw_data",
              "destination": "raw_data.csv"
            }
          ]
        },
        "output": {
          "tables": [
            {
              "source": "processed_data.csv",
              "destination": "out.c-data.processed_data"
            }
          ]
        }
      }
    }
  }'
```

<details>
<summary>Deep Dive: Input/Output Mapping Explained</summary>

**Input Mapping:**

Maps Storage tables to files in the component's `/data/in/tables/` directory:

```json
{
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-data.customers",      // Storage table ID
          "destination": "customers.csv",        // Local file name
          "columns": ["id", "name", "email"],    // Optional: select columns
          "where_column": "status",              // Optional: filter rows
          "where_values": ["active"],
          "where_operator": "eq",
          "days": 7                              // Optional: only recent data
        }
      ]
    }
  }
}
```

Component reads: `/data/in/tables/customers.csv`

**Output Mapping:**

Maps files from `/data/out/tables/` to Storage tables:

```json
{
  "storage": {
    "output": {
      "tables": [
        {
          "source": "results.csv",                    // Local file name
          "destination": "out.c-analysis.results",    // Storage table ID
          "primary_key": ["date", "product"],         // Optional
          "incremental": true,                        // Append vs replace
          "delete_where_column": "date",              // Optional: delete old data
          "delete_where_values": ["2024-01-01"],
          "delete_where_operator": "lt"
        }
      ]
    }
  }
}
```

**File Manifests (Alternative to Mapping):**

Components can write `.manifest` files to control output:

```python
# Create customers.csv.manifest
import json

manifest = {
    "destination": "out.c-data.customers",
    "primary_key": ["id"],
    "incremental": False,
    "metadata": [
        {
            "key": "processed_date",
            "value": "2024-01-15"
        }
    ]
}

with open("/data/out/tables/customers.csv.manifest", "w") as f:
    json.dump(manifest, f)
```

Manifests override output mapping configuration.

</details>

### Testing Components Locally

```bash
# Create test data structure
mkdir -p data/in/tables data/out/tables

# Create config.json
cat > data/config.json <<EOF
{
  "parameters": {
    "db": {
      "host": "localhost",
      "port": 3306
    }
  }
}
EOF

# Create input data
cat > data/in/tables/input.csv <<EOF
id,value
1,100
2,200
EOF

# Run component
docker run --rm \
  -v $(pwd)/data:/data \
  my-dockerhub-username/my-component:1.0.0

# Check output
cat data/out/tables/processed_input.csv
```

## Flows Orchestration

Flows (formerly Orchestrations) manage the execution order of components.

### Flow Structure

```yaml
name: Daily ETL Pipeline
tasks:
  - id: extract_mysql
    component: keboola.ex-db-mysql
    config: mysql_production

  - id: extract_postgres
    component: keboola.ex-db-pgsql
    config: postgres_production

  - id: transform_data
    component: keboola.snowflake-transformation
    config: main_transformation
    dependencies:
      - extract_mysql
      - extract_postgres

  - id: write_to_gsheets
    component: keboola.wr-google-sheets
    config: daily_report
    dependencies:
      - transform_data

schedule:
  cron: "0 2 * * *"  # Run at 2 AM daily
  timezone: "America/New_York"
```

### Triggering Flows via API

```python
# Run a flow
response = requests.post(
    f"{base_url}/v2/storage/orchestrations/123456/run",
    headers=headers
)

orchestration_job_id = response.json()["id"]

# Monitor flow execution
response = requests.get(
    f"{base_url}/v2/storage/jobs/{orchestration_job_id}",
    headers=headers
)

# Get individual task jobs
flow_result = response.json()
task_jobs = flow_result.get("results", {}).get("tasks", [])

for task in task_jobs:
    print(f"Task: {task['name']}")
    print(f"  Status: {task['status']}")
    print(f"  Job ID: {task['jobId']}")
```

### Flow Best Practices

1. **Use Dependencies**: Chain tasks with `dependencies` for proper execution order
2. **Set Timeouts**: Configure max execution time for each task
3. **Enable Notifications**: Get alerts on success/failure
4. **Use Phases**: Group related tasks into logical phases
5. **Test Manually**: Run flows manually before scheduling

<details>
<summary>Deep Dive: Advanced Flow Patterns</summary>

**Conditional Execution:**

```json
{
  "tasks": [
    {
      "id": "check_data",
      "component": "my-vendor.data-validator",
      "config": "validation_config"
    },
    {
      "id": "process_data",
      "component": "keboola.snowflake-transformation",
      "config": "main_transform",
      "dependencies": ["check_data"],
      "continueOnFailure": false
    }
  ]
}
```

**Parallel Execution:**

```json
{
  "tasks": [
    {
      "id": "extract_source_a",
      "component": "keboola.ex-db-mysql",
      "config": "source_a"
    },
    {
      "id": "extract_source_b",
      "component": "keboola.ex-db-pgsql",
      "config": "source_b"
    },
    {
      "id": "merge_data",
      "component": "keboola.snowflake-transformation",
      "config": "merge_transform",
      "dependencies": ["extract_source_a", "extract_source_b"]
    }
  ]
}
```

Tasks without dependencies run in parallel.

**Retry Logic:**

```json
{
  "tasks": [
    {
      "id": "flaky_api_call",
      "component": "my-vendor.api-extractor",
      "config": "api_config",
      "retryConfig": {
        "maxRetries": 3,
        "initialDelay": 60,
        "backoffMultiplier": 2
      }
    }
  ]
}
```

</details>

## MCP Server Integration

The Keboola MCP server provides AI-friendly access to Keboola operations.

### When to Use MCP vs Custom Code

**Use MCP Server When:**
- Validating data structures before writing code
- Querying small datasets for analysis (< 10,000 rows)
- Checking table schemas and metadata
- Prototyping and exploring data
- Interactive development and debugging

**Use Custom Code/Components When:**
- Processing large datasets (> 10,000 rows)
- Complex transformations with custom business logic
- Production ETL pipelines
- Integration with external systems
- Scheduled recurring operations

### MCP Server Operations

**Available Operations:**

```python
# Project Information
mcp__keboola__get_project_info()
# Returns: project ID, region, SQL dialect, storage backend

# List Tables
mcp__keboola__list_tables(bucket_id="out.c-analysis")
# Returns: array of tables in bucket

# Get Table Details
mcp__keboola__get_table(table_id="out.c-analysis.sales_data")
# Returns: schema, row count, size, column types

# Query Data
mcp__keboola__query_data(
    sql='SELECT * FROM "KBC_USE4_361"."out.c-analysis"."sales_data" LIMIT 100',
    query_name="Sales Sample"
)
# Returns: query results as structured data

# Search
mcp__keboola__search(query="customer data")
# Returns: tables, configs, and other objects matching query

# List Components
mcp__keboola__list_components(type="extractor")
# Returns: available components filtered by type
```

**Authentication:**

The MCP server uses OAuth for authentication. When first used, you'll be prompted to:
1. Visit an authorization URL
2. Grant access to your Keboola project
3. Token is stored for future use

### MCP Best Practices

1. **Always validate before coding**: Use `get_table` to check schemas
2. **Test SQL queries first**: Use `query_data` to verify syntax
3. **Check data volumes**: Use `get_table` row counts before loading
4. **Use fully qualified names**: Get from `get_table` response
5. **Limit query results**: Always use `LIMIT` for exploratory queries

<details>
<summary>Deep Dive: MCP Server Architecture</summary>

**How MCP Works:**

```
Claude Code → MCP Client → MCP Server → Keboola API → Keboola Backend
```

1. You call MCP function (e.g., `mcp__keboola__get_table`)
2. MCP client sends request to MCP server
3. MCP server authenticates with Keboola
4. MCP server calls appropriate Keboola API
5. Results are formatted and returned

**MCP Server Endpoints:**

The Keboola MCP server exposes:

- **Resources**: Static information (project info, component list)
- **Tools**: Actions (query data, run jobs, create tables)
- **Prompts**: Guided workflows (not yet implemented)

**Configuration:**

MCP server is configured in Claude Code's settings:

```json
{
  "mcpServers": {
    "keboola": {
      "url": "https://mcp.us-east4.gcp.keboola.com/mcp",
      "transport": "http",
      "oauth": {
        "clientId": "your-client-id",
        "tokenUrl": "https://connection.keboola.com/oauth/token"
      }
    }
  }
}
```

**Rate Limits:**

The MCP server has rate limits:
- 100 requests per minute per user
- 10 concurrent query executions
- Query timeout: 60 seconds

For production use, use direct API calls or custom components.

</details>

## Common Pitfalls and Solutions

### Pitfall 1: Workspace ID Confusion

**Problem**: User provides wrong ID type for API calls

**Solution**:
```python
# ❌ WRONG: Using storage backend ID for API calls
project_id = "KBC_USE4_361"  # This is internal DB name!

# ✅ CORRECT: Use numeric project ID
project_id = 12345  # From URL or get_project_info
```

**How to help users**:
1. Ask them to check their URL: `connection.keboola.com/admin/projects/[PROJECT_ID]`
2. Use `mcp__keboola__get_project_info` to confirm
3. Explain the different ID types (see "Workspace ID Confusion" section above)

### Pitfall 2: Input/Output Mapping Confusion

**Problem**: User doesn't understand how data gets in/out of component

**Solution**:

```
Business Language → Keboola Operations

"I want to read customer data" →
  Input mapping: in.c-data.customers → /data/in/tables/customers.csv

"I want to save results" →
  Output mapping: /data/out/tables/results.csv → out.c-analysis.results
  OR write manifest file
```

**Teaching approach**:
1. Explain that components run in isolated containers
2. Show the `/data` directory structure
3. Walk through mapping configuration
4. Emphasize: Storage table ID ↔ Local file path

### Pitfall 3: Primary Key Behavior Misunderstanding

**Problem**: User expects UPDATE but gets duplicates (or vice versa)

**Solution**:

```python
# With primary key + incremental: UPSERT behavior
{
  "destination": "out.c-data.customers",
  "primary_key": ["customer_id"],
  "incremental": True
}
# → Matching rows updated, new rows inserted

# Without primary key + incremental: APPEND behavior
{
  "destination": "out.c-data.events",
  "incremental": True
}
# → All rows appended (can create duplicates!)

# Without incremental: REPLACE behavior
{
  "destination": "out.c-data.snapshot",
  "incremental": False
}
# → Table truncated and replaced with new data
```

### Pitfall 4: Querying Without Fully Qualified Names

**Problem**: SQL query fails with "table not found"

**Solution**:

```sql
-- ❌ WRONG: Using table ID in SQL
SELECT * FROM "out.c-analysis.sales_data"

-- ✅ CORRECT: Using fully qualified name
SELECT * FROM "KBC_USE4_361"."out.c-analysis"."sales_data"
```

**How to help**:
1. Use `mcp__keboola__get_table` to get fully qualified name
2. Explain: Table ID is for API, FQN is for SQL
3. Show the format: `"[BACKEND_ID]"."[BUCKET_NAME]"."[TABLE_NAME]"`

### Pitfall 5: Forgetting to Quote SQL Identifiers

**Problem**: SQL errors due to case sensitivity or reserved words

**Solution**:

```sql
-- ❌ WRONG: Unquoted identifiers
SELECT date, order FROM sales WHERE status = active

-- ✅ CORRECT: Quoted identifiers
SELECT "date", "order" FROM "sales" WHERE "status" = 'active'
```

**Best practice**: Always quote table and column names in Snowflake/BigQuery.

### Pitfall 6: Not Checking Job Status

**Problem**: Component appears to hang or fail silently

**Solution**:

```python
# ❌ WRONG: Fire and forget
requests.post(f"{base_url}/v2/storage/components/{comp}/configs/{cfg}/run")
# What if it fails?

# ✅ CORRECT: Monitor job status
response = requests.post(...)
job_id = response.json()["id"]
result = wait_for_job(job_id)  # Polls until complete or fails
if result["status"] == "success":
    print("Success!")
else:
    print(f"Failed: {result['error']['message']}")
```

### Pitfall 7: Loading Large Tables with MCP

**Problem**: MCP query times out or returns truncated results

**Solution**:

```python
# ❌ WRONG: Query millions of rows via MCP
mcp__keboola__query_data(
    sql='SELECT * FROM "KBC_USE4_361"."out.c-data"."huge_table"'
)
# Times out after 60 seconds!

# ✅ CORRECT: Use for validation only
mcp__keboola__query_data(
    sql='SELECT * FROM "KBC_USE4_361"."out.c-data"."huge_table" LIMIT 100'
)
# Then use Storage API export or transformation for processing
```

**Rule of thumb**: MCP for < 10k rows, API/components for larger datasets.

## Working Code Examples

### Example 1: Complete ETL Script

```python
#!/usr/bin/env python3
"""
Complete ETL: Extract from MySQL, Transform in Python, Load to Keboola
"""
import requests
import mysql.connector
import csv
import os

# Configuration
# IMPORTANT: Set KEBOOLA_STACK_URL to your region's stack
# US: connection.keboola.com
# EU: connection.eu-central-1.keboola.com
# Azure: connection.north-europe.azure.keboola.com
KEBOOLA_STACK_URL = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
KEBOOLA_PROJECT_ID = 12345
KEBOOLA_TOKEN = os.environ["KEBOOLA_TOKEN"]
KEBOOLA_URL = f"https://{KEBOOLA_STACK_URL}"

MYSQL_HOST = "mysql.example.com"
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_DB = "sales"

# Headers for Keboola API
headers = {
    "X-StorageApi-Token": KEBOOLA_TOKEN,
    "Content-Type": "application/json"
}

def extract_from_mysql(query, output_file):
    """Extract data from MySQL to CSV."""
    print(f"Extracting data from MySQL...")

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)

    rows = cursor.fetchall()

    if rows:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    cursor.close()
    conn.close()

    print(f"Extracted {len(rows)} rows to {output_file}")
    return len(rows)

def transform_data(input_file, output_file):
    """Transform data: calculate revenue, filter invalid rows."""
    print(f"Transforming data...")

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    transformed = []
    for row in rows:
        # Calculate revenue
        quantity = int(row['quantity'])
        price = float(row['price'])
        revenue = quantity * price

        # Filter out zero-revenue rows
        if revenue > 0:
            row['revenue'] = revenue
            transformed.append(row)

    with open(output_file, 'w', newline='') as f:
        if transformed:
            writer = csv.DictWriter(f, fieldnames=transformed[0].keys())
            writer.writeheader()
            writer.writerows(transformed)

    print(f"Transformed {len(transformed)} rows to {output_file}")
    return len(transformed)

def load_to_keboola(file_path, table_id, primary_key=None):
    """Load CSV to Keboola Storage."""
    print(f"Loading data to Keboola table {table_id}...")

    # Parse bucket and table name
    parts = table_id.split('.')
    bucket_id = '.'.join(parts[:2])  # e.g., "out.c-data"
    table_name = parts[2]

    # Upload file
    with open(file_path, 'rb') as f:
        files = {'dataFile': f}
        data = {
            'name': table_name,
            'delimiter': ',',
            'enclosure': '"'
        }

        if primary_key:
            data['primaryKey[]'] = primary_key

        response = requests.post(
            f"{KEBOOLA_URL}/v2/storage/buckets/{bucket_id}/tables-async",
            headers={k: v for k, v in headers.items() if k != 'Content-Type'},
            data=data,
            files=files
        )

        response.raise_for_status()
        job_id = response.json()["id"]

    # Wait for job
    import time
    while True:
        response = requests.get(
            f"{KEBOOLA_URL}/v2/storage/jobs/{job_id}",
            headers=headers
        )
        job = response.json()

        if job["status"] == "success":
            print(f"Successfully loaded to {table_id}")
            return job
        elif job["status"] in ["error", "cancelled"]:
            raise Exception(f"Load failed: {job.get('error', {}).get('message')}")

        time.sleep(2)

def main():
    """Main ETL pipeline."""
    try:
        # Step 1: Extract
        extract_query = """
            SELECT
                order_id,
                product,
                quantity,
                price,
                order_date
            FROM orders
            WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """

        raw_file = "/tmp/raw_orders.csv"
        extract_from_mysql(extract_query, raw_file)

        # Step 2: Transform
        transformed_file = "/tmp/transformed_orders.csv"
        transform_data(raw_file, transformed_file)

        # Step 3: Load
        load_to_keboola(
            transformed_file,
            "out.c-sales.weekly_orders",
            primary_key=["order_id"]
        )

        print("ETL pipeline completed successfully!")

    except Exception as e:
        print(f"ETL pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

### Example 2: Orchestration with Error Handling

```python
#!/usr/bin/env python3
"""
Run a Keboola Flow with comprehensive error handling and notifications.
"""
import requests
import time
import os

# Use your stack URL - find it from your Keboola login URL domain
KEBOOLA_STACK_URL = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
KEBOOLA_URL = f"https://{KEBOOLA_STACK_URL}"
KEBOOLA_TOKEN = os.environ["KEBOOLA_TOKEN"]
ORCHESTRATION_ID = 123456

headers = {
    "X-StorageApi-Token": KEBOOLA_TOKEN,
    "Content-Type": "application/json"
}

def send_notification(subject, message, status="info"):
    """Send notification (implement your notification method)."""
    print(f"[{status.upper()}] {subject}")
    print(f"  {message}")
    # Add Slack/email notification here

def run_orchestration(orchestration_id, max_wait_seconds=3600):
    """Run orchestration and wait for completion."""

    # Start orchestration
    print(f"Starting orchestration {orchestration_id}...")

    response = requests.post(
        f"{KEBOOLA_URL}/v2/storage/orchestrations/{orchestration_id}/run",
        headers=headers
    )
    response.raise_for_status()

    job_id = response.json()["id"]
    print(f"Orchestration job started: {job_id}")

    # Monitor execution
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait_seconds:
        response = requests.get(
            f"{KEBOOLA_URL}/v2/storage/jobs/{job_id}",
            headers=headers
        )
        response.raise_for_status()

        job = response.json()
        status = job["status"]

        # Log status changes
        if status != last_status:
            print(f"Status: {status}")
            last_status = status

        # Check completion
        if status == "success":
            duration = time.time() - start_time

            # Get task details
            tasks = job.get("results", {}).get("tasks", [])

            success_message = f"Orchestration completed in {duration:.1f} seconds\n"
            success_message += f"Tasks executed: {len(tasks)}\n"

            for task in tasks:
                success_message += f"  - {task['name']}: {task['status']}\n"

            send_notification(
                f"Orchestration {orchestration_id} Succeeded",
                success_message,
                "success"
            )

            return job

        elif status in ["error", "cancelled", "terminated"]:
            # Get error details
            error_msg = job.get("error", {}).get("message", "Unknown error")

            # Get failed task details
            tasks = job.get("results", {}).get("tasks", [])
            failed_tasks = [t for t in tasks if t["status"] == "error"]

            error_details = f"Orchestration failed: {error_msg}\n"
            error_details += f"Failed tasks: {len(failed_tasks)}\n"

            for task in failed_tasks:
                error_details += f"  - {task['name']}\n"

                # Get task job logs
                task_job_id = task.get("jobId")
                if task_job_id:
                    log_response = requests.get(
                        f"{KEBOOLA_URL}/v2/storage/jobs/{task_job_id}/events",
                        headers=headers
                    )
                    if log_response.ok:
                        events = log_response.json()
                        error_events = [e for e in events if e.get("type") == "error"]
                        if error_events:
                            error_details += f"    Error: {error_events[0]['message']}\n"

            send_notification(
                f"Orchestration {orchestration_id} Failed",
                error_details,
                "error"
            )

            raise Exception(f"Orchestration failed: {error_msg}")

        time.sleep(10)

    # Timeout
    send_notification(
        f"Orchestration {orchestration_id} Timeout",
        f"Did not complete within {max_wait_seconds} seconds",
        "error"
    )
    raise TimeoutError(f"Orchestration did not complete in {max_wait_seconds} seconds")

def main():
    """Main execution."""
    try:
        result = run_orchestration(ORCHESTRATION_ID)
        print(f"Orchestration completed successfully!")
        print(f"Job ID: {result['id']}")

    except Exception as e:
        print(f"Orchestration execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

### Example 3: Data Validation Before Processing

```python
#!/usr/bin/env python3
"""
Validate data quality before running downstream processes.
Uses MCP for validation, then triggers processing if data is good.
"""
import sys

def validate_data_structure():
    """Validate that required tables exist with correct schema."""
    print("Validating data structure...")

    required_tables = [
        {
            "table_id": "in.c-data.customers",
            "required_columns": ["customer_id", "name", "email", "created_date"]
        },
        {
            "table_id": "in.c-data.orders",
            "required_columns": ["order_id", "customer_id", "amount", "order_date"]
        }
    ]

    errors = []

    for table_spec in required_tables:
        table_id = table_spec["table_id"]

        # Check table exists and get schema
        # (In real code, use mcp__keboola__get_table)
        # table = mcp__keboola__get_table(table_id)

        # Simulate MCP call result
        table = {
            "id": table_id,
            "columns": ["customer_id", "name", "email", "created_date", "extra_field"]
        }

        # Check required columns
        missing_columns = [
            col for col in table_spec["required_columns"]
            if col not in table["columns"]
        ]

        if missing_columns:
            errors.append(
                f"Table {table_id} missing columns: {', '.join(missing_columns)}"
            )

    if errors:
        print("Data structure validation FAILED:")
        for error in errors:
            print(f"  ❌ {error}")
        return False

    print("Data structure validation PASSED ✅")
    return True

def validate_data_quality():
    """Validate data quality rules."""
    print("Validating data quality...")

    # Query for quality checks
    # (In real code, use mcp__keboola__query_data)

    checks = [
        {
            "name": "Check for NULL emails",
            "sql": '''
                SELECT COUNT(*) as null_count
                FROM "KBC_USE4_361"."in.c-data"."customers"
                WHERE "email" IS NULL
            ''',
            "threshold": 0  # No NULLs allowed
        },
        {
            "name": "Check for duplicate customer IDs",
            "sql": '''
                SELECT "customer_id", COUNT(*) as count
                FROM "KBC_USE4_361"."in.c-data"."customers"
                GROUP BY "customer_id"
                HAVING COUNT(*) > 1
            ''',
            "threshold": 0  # No duplicates
        },
        {
            "name": "Check for recent data",
            "sql": '''
                SELECT COUNT(*) as recent_count
                FROM "KBC_USE4_361"."in.c-data"."orders"
                WHERE "order_date" >= CURRENT_DATE - INTERVAL '7 days'
            ''',
            "threshold": 1  # At least 1 recent order
        }
    ]

    errors = []

    for check in checks:
        # Simulate query result
        # result = mcp__keboola__query_data(check["sql"], check["name"])

        # For demonstration, simulate passing checks
        result_value = 0  # Assume checks pass

        if result_value > check["threshold"]:
            errors.append(f"{check['name']} failed: {result_value} issues found")

    if errors:
        print("Data quality validation FAILED:")
        for error in errors:
            print(f"  ❌ {error}")
        return False

    print("Data quality validation PASSED ✅")
    return True

def trigger_processing():
    """Trigger downstream processing components."""
    print("Triggering processing pipeline...")

    # Run transformations, orchestrations, etc.
    # (Use Jobs API as shown in previous examples)

    print("Processing triggered successfully ✅")
    return True

def main():
    """Main validation and processing workflow."""
    print("=" * 60)
    print("Data Validation and Processing Pipeline")
    print("=" * 60)

    # Step 1: Validate structure
    if not validate_data_structure():
        print("\n❌ Pipeline aborted: Data structure validation failed")
        sys.exit(1)

    # Step 2: Validate quality
    if not validate_data_quality():
        print("\n❌ Pipeline aborted: Data quality validation failed")
        sys.exit(1)

    # Step 3: Trigger processing
    print("\n✅ All validations passed, starting processing...")

    if not trigger_processing():
        print("\n❌ Processing failed")
        sys.exit(1)

    print("\n✅ Pipeline completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

## Summary: Key Takeaways

### For End-Users (Business Language → Keboola Operations)

| Business Need | Keboola Operation |
|---------------|-------------------|
| "I want to connect to our database" | Create extractor configuration |
| "I need to transform the data" | Create transformation (SQL/Python) |
| "Save results to Google Sheets" | Create writer configuration |
| "Run this every morning" | Create orchestration/flow with schedule |
| "I need to test changes safely" | Create development branch |
| "Make this data available to others" | Write to output bucket (`out.c-*`) |

### For Developers

1. **Always use MCP for validation first** before writing production code
2. **Monitor job status** - never fire and forget
3. **Use fully qualified names** in SQL queries
4. **Quote all identifiers** to avoid case sensitivity issues
5. **Understand input/output mapping** - it's your data interface
6. **Set primary keys** for upsert behavior
7. **Handle errors gracefully** with retries and notifications
8. **Test locally** before deploying components
9. **Use Storage API** for large dataset operations
10. **Leverage orchestrations** to chain operations properly

### Quick Reference Card

```
Stack URL (Regional Endpoint):
  US: connection.keboola.com
  EU: connection.eu-central-1.keboola.com
  Find yours: Check your login URL domain
  From MCP: mcp__keboola__get_project_info()["stack"]

Authentication:
  Storage API: X-StorageApi-Token header
  MCP Server: OAuth (prompted on first use)
  Token Scope: Bound to specific project AND stack

Project ID:
  From URL: https://{stack-url}/admin/projects/[ID]
  From MCP: mcp__keboola__get_project_info()["id"]

Table Operations:
  Read: GET /v2/storage/tables/{table_id}/export-async
  Write: POST /v2/storage/buckets/{bucket_id}/tables-async
  Query: mcp__keboola__query_data(sql)

Job Operations:
  Run: POST /v2/storage/components/{comp}/configs/{cfg}/run
  Status: GET /v2/storage/jobs/{job_id}
  Logs: GET /v2/storage/jobs/{job_id}/events

Component Development:
  Structure: src/component.py + Dockerfile + requirements.txt
  Interface: keboola.component.CommonInterface
  Input: /data/in/tables/*.csv
  Output: /data/out/tables/*.csv + .manifest files
```

## Additional Resources

- [Keboola Developer Portal](https://developers.keboola.com)
- [Storage API Documentation](https://keboola.docs.apiary.io)
- [Component Development Guide](https://developers.keboola.com/extend/component/)
- [Python Component Library](https://github.com/keboola/python-component)
- [Keboola MCP Server](https://github.com/keboola/mcp-server-keboola)

---

## Error Reporting Protocol

### When Users Report Problems

If a user says your solution doesn't work or asks for help with an error:

#### Step 1: Gather Context (ALWAYS FIRST)

Ask specific questions:
- "What's the exact error message?"
- "Can you share the code/config you're using?"
- "What environment is this? (local, Custom Python, etc.)"
- "What did you expect vs what happened?"

#### Step 2: Analyze Root Cause

**User Error Indicators** (DO NOT REPORT):
- Permission denied / 401/403 errors → Token/permissions issue
- Module not found → Missing dependency
- Network errors → Environment/connectivity
- Variables undefined → Code needs adaptation
- Wrong table names → User's specific setup

**Action**: Help fix the user error. Don't create issues.

**Knowledge Gap Indicators** (OFFER TO REPORT):
- You don't know the answer
- SKILL.md doesn't cover the scenario
- Multiple users ask the same thing
- Keboola has a feature you're unaware of

**Action**: After trying to help, suggest creating issue.

**Documentation Bug Indicators** (STRONGLY RECOMMEND REPORTING):
- Official docs contradict your information
- API has changed (user shows evidence)
- Code examples don't work with correct setup
- Features work differently than described

**Action**: Recommend creating issue with evidence.

#### Step 3: Attempt to Fix (2-3 Tries)

Try different approaches before escalating:
1. Fix obvious issues
2. Check alternative methods
3. Research in Keboola docs

#### Step 4: Decision Point

After 2-3 attempts:

**If User Error:**
"I've helped you fix [issue]. This was related to [explanation]. Let me know if you have other questions!"

**If Knowledge Gap:**
"I notice I don't have information about [topic]. This would be valuable to add.

Should I create an issue so this gets documented? It would help future users with the same question."

**Wait for confirmation.**

**If Documentation Bug:**
"The documentation I have appears outdated. According to [official source], the correct approach is [X], but I suggested [Y].

I should create an issue to fix this. Should I proceed?"

**Strongly recommend, but wait for confirmation.**

#### Step 5: Create Issue (Only If Confirmed)

When user confirms, explain what you're doing:

"I'll create an issue to track this. The team will review and update the knowledge base. Thanks for helping improve the documentation!"

Then use: `./hooks/error-reporter.sh` with appropriate details.

### What NOT to Report

❌ User environment issues (permissions, network, packages)
❌ User's code adaptation mistakes
❌ Questions you can already answer
❌ Feature requests for things that don't exist
❌ General programming questions

### What TO Report

✅ Information missing from this SKILL that should be here
✅ Outdated/incorrect information (with evidence)
✅ Broken links to Keboola docs
✅ Code examples that don't work
✅ Patterns multiple users struggle with
✅ New Keboola features not documented

### Key Principles

1. **Gather details first** - Never assume
2. **Try to fix first** - At least 2-3 attempts
3. **Distinguish** user errors from knowledge gaps
4. **Always ask permission** - Never auto-report
5. **Be transparent** - Explain why reporting
6. **Thank users** - They improve the system

---

**Remember**: When in doubt, validate with MCP first, then build with confidence!

### Stack URL: Your Regional API Endpoint

**What is a Stack URL?**

Keboola operates multiple regional deployments ("stacks") across the world. Each stack has its own base URL that serves as the foundation for all API calls. The Stack URL is **separate from and independent of** your Project ID.

**Key Distinction:**
- **Stack URL**: The regional API endpoint (e.g., `connection.keboola.com`)
- **Project ID**: Your specific project identifier (e.g., `12345`)

You need **both** to make API calls: `https://{STACK_URL}/v2/storage/...`

#### Available Regional Stacks

| Region | Stack URL | Location |
|--------|-----------|----------|
| US | `connection.keboola.com` | AWS US East (Virginia) |
| EU | `connection.eu-central-1.keboola.com` | AWS EU Central (Frankfurt) |
| Azure North Europe | `connection.north-europe.azure.keboola.com` | Azure North Europe (Ireland) |

#### How to Find Your Stack URL

**Method 1: Check Your Login URL**

Your Stack URL is the domain you use to log into Keboola:

```
https://connection.keboola.com/admin/projects/12345/...
         ^^^^^^^^^^^^^^^^^^^^^^^
         This is your Stack URL
```

**Method 2: Use MCP Server**

```python
# Get project info including stack details
project_info = mcp__keboola__get_project_info()

# Returns:
# {
#   "id": 12345,
#   "url": "https://connection.keboola.com",
#   "stack": "connection.keboola.com",
#   "backend": "snowflake",
#   ...
# }

stack_url = project_info["stack"]
```

**Method 3: Ask Your Keboola Administrator**

If you're unsure, contact your Keboola administrator or check your onboarding documentation.

#### Using Stack URL in API Calls

**❌ WRONG: Hardcoded regional URL**
```python
base_url = "https://connection.keboola.com"  # Only works for US region!
```

**✅ CORRECT: Configurable Stack URL**
```python
# Store as configuration
STACK_URL = "connection.eu-central-1.keboola.com"  # EU region
PROJECT_ID = 12345
STORAGE_TOKEN = "your-token"

base_url = f"https://{STACK_URL}"

# Make API calls
response = requests.get(
    f"{base_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": STORAGE_TOKEN}
)
```

**Best Practice Pattern:**
```python
import os

# Load from environment variables
STACK_URL = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
PROJECT_ID = os.environ["KEBOOLA_PROJECT_ID"]
STORAGE_TOKEN = os.environ["KEBOOLA_TOKEN"]

base_url = f"https://{STACK_URL}"
```

#### Stack URL in MCP Server

The MCP server automatically determines your Stack URL during OAuth authentication. You don't need to configure it manually when using MCP functions.

#### Common Mistakes

**Mistake 1: Using US Stack for EU Project**
```python
# EU project trying to use US stack
base_url = "https://connection.keboola.com"  # Wrong stack!
response = requests.get(
    f"{base_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": eu_project_token}
)
# Returns: 401 Unauthorized or 404 Not Found
```

**Mistake 2: Confusing Stack URL with Project ID**
```python
# Don't use Project ID as part of the base URL
base_url = f"https://connection.keboola.com/projects/{PROJECT_ID}"  # Wrong!

# Project ID is used in specific endpoints, not the base URL
base_url = f"https://{STACK_URL}"  # Correct base
endpoint = f"{base_url}/v2/storage/projects/{PROJECT_ID}/..."  # When needed
```

**Mistake 3: Mixing Stack URLs**
```python
# Don't mix different regional endpoints in the same script
read_url = "https://connection.keboola.com"
write_url = "https://connection.eu-central-1.keboola.com"
# These are completely separate Keboola instances!
```

<details>
<summary>Deep Dive: Stack Architecture and Token Scope</summary>

**Stack Isolation:**

Each Keboola stack is a completely independent deployment:
- Separate databases
- Separate user accounts
- Separate projects
- Separate API tokens

A token from the US stack will **never** work with the EU stack, even if you have projects in both regions.

**Token-Stack Binding:**

When you create a Storage API token, it's bound to:
1. A specific project
2. On a specific stack
3. With specific permissions

Example:
```
Token: abc123...
Project: 12345
Stack: connection.eu-central-1.keboola.com
Scope: storage:read, storage:write
```

This token:
- ✅ Works with: `https://connection.eu-central-1.keboola.com`
- ❌ Fails with: `https://connection.keboola.com` (different stack)
- ❌ Fails with: Project 67890 (different project)

**Multi-Region Organizations:**

Some organizations have projects across multiple stacks. Each project requires:
- Its own Stack URL
- Its own Project ID
- Its own API token

Managing multi-region setup:
```python
PROJECTS = [
    {
        "name": "US Production",
        "stack": "connection.keboola.com",
        "project_id": 12345,
        "token": os.environ["KEBOOLA_TOKEN_US"]
    },
    {
        "name": "EU Production",
        "stack": "connection.eu-central-1.keboola.com",
        "project_id": 67890,
        "token": os.environ["KEBOOLA_TOKEN_EU"]
    }
]

for project in PROJECTS:
    base_url = f"https://{project['stack']}"
    # Make API calls with project-specific configuration
```

</details>

### Pitfall 8: Using Wrong Stack URL

**Problem**: API calls fail with 401/404 errors despite valid token

**Solution**:

```python
# ❌ WRONG: EU project using US stack URL
stack_url = "connection.keboola.com"  # US stack
eu_token = "your-eu-project-token"

response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": eu_token}
)
# Returns: 401 Unauthorized - token not found

# ✅ CORRECT: Match stack URL to your project's region
stack_url = "connection.eu-central-1.keboola.com"  # EU stack
eu_token = "your-eu-project-token"

response = requests.get(
    f"https://{stack_url}/v2/storage/tables",
    headers={"X-StorageApi-Token": eu_token}
)
# Success!
```

**How to diagnose**:

1. Check your Keboola login URL:
   - If you log in at `connection.eu-central-1.keboola.com` → Use EU stack
   - If you log in at `connection.keboola.com` → Use US stack

2. Use MCP to verify:
```python
project_info = mcp__keboola__get_project_info()
print(f"Your stack: {project_info['stack']}")
```

3. Look for these error patterns:
   - `401 Unauthorized` + valid token = wrong stack
   - `404 Not Found` + existing table = wrong stack
   - Connection timeout = wrong stack (network routing failure)

**Prevention**:

Always use environment variables for stack configuration:

```python
import os

# Required environment variables:
# KEBOOLA_STACK_URL - Your region's stack (e.g., connection.eu-central-1.keboola.com)
# KEBOOLA_TOKEN - Your project's API token

STACK_URL = os.environ["KEBOOLA_STACK_URL"]  # Fail fast if not set
base_url = f"https://{STACK_URL}"

# Now all API calls use the correct region
```
