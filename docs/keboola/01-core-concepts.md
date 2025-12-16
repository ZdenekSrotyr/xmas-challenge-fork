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

## Working with Keboola: MCP vs API

Keboola provides two complementary ways to interact with your data:

### MCP Server (Model Context Protocol)

The Keboola MCP server provides high-level tools for interactive development:
- **Best for**: Prototyping, validation, schema inspection, debugging
- **Authentication**: OAuth (browser-based, interactive)
- **Tools**: `get_table`, `query_data`, `list_tables`, `get_job`, etc.
- **Use when**: Developing locally, validating data structures, exploring tables

**Example use case**: Before writing a data pipeline, use MCP to validate table schemas and test SQL queries interactively.

### Storage API (REST)

The Storage API provides low-level REST endpoints for production use:
- **Best for**: Production pipelines, automation, large datasets, scheduled jobs
- **Authentication**: Storage API token
- **Operations**: Export/import tables, manage buckets, job polling
- **Use when**: Building production code, processing large datasets, CI/CD

**Example use case**: Automated ETL pipeline that exports tables on a schedule.

### Recommended Workflow

1. **Validate with MCP**: Check schemas, test queries, verify data structure
2. **Build with Storage API**: Implement production pipeline with proper error handling
3. **Deploy with confidence**: Code works first time because structure was validated

For detailed guidance on choosing between MCP and Storage API, see the [MCP vs API Guide](04-mcp-vs-api.md).
