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

## Keboola MCP Server

For development and prototyping, Keboola provides an MCP (Model Context Protocol) server with interactive tools:

- **Schema validation**: Check table structures without writing code
- **Query testing**: Prototype SQL queries interactively
- **Job debugging**: Inspect job status and errors
- **Data exploration**: Quick data samples and analysis

**Setup**: OAuth authentication (automatic on first use)
**Access**: Available through Claude Desktop and MCP-compatible tools

**Example MCP tools:**
```python
# Get table schema
mcp__keboola__get_table("in.c-main.customers")

# Test query
mcp__keboola__query_data(
    sql_query='SELECT * FROM "DATABASE"."SCHEMA"."customers" LIMIT 10'
)

# Check job status
mcp__keboola__get_job(job_id="123456789")
```

**When to use**: See [MCP Server vs Direct API Usage](04-mcp-vs-api.md) for detailed guidance.

**Note**: MCP is designed for development workflows. For production pipelines, use the Storage API directly.

## Regional Stacks

Keboola operates multiple regional stacks:
- **US**: connection.keboola.com
- **EU**: connection.eu-central-1.keboola.com
- **Azure**: connection.north-europe.azure.keboola.com

Always use your project's stack URL, not a hardcoded one.
