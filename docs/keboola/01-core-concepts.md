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

## Access Methods

There are multiple ways to interact with Keboola:

### MCP Server (Model Context Protocol)
A Claude AI integration providing high-level tools for data exploration:
- Best for: Interactive data exploration, prototyping, validation
- Authentication: OAuth (one-time setup)
- Data limits: Suitable for tables under ~1000 rows
- See `04-mcp-vs-api.md` for detailed guidance

### Storage API
Direct HTTP REST API for programmatic access:
- Best for: Production pipelines, large datasets, automated workflows
- Authentication: API token per request
- Data limits: No limits (supports pagination)
- See `02-storage-api.md` for implementation details

### Components
Platform-managed data processing modules:
- Best for: Scheduled workflows, complex transformations, external integrations
- Authentication: Managed by platform
- See component developer documentation

**Need help choosing?** See `04-mcp-vs-api.md` for a complete comparison and decision framework.
