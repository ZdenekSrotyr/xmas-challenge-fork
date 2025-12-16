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
- **Transformations**: Process and modify data (see [Custom Python Components](04-custom-components.md))
- **Writers**: Send data to external destinations

#### Two Approaches to Working with Keboola

1. **Direct Storage API Calls** (covered in [Storage API](02-storage-api.md))
   - Use REST API directly with HTTP requests
   - Good for one-off scripts, external orchestration, quick prototypes
   - Requires manual handling of I/O, authentication, job polling

2. **Custom Python Components** (covered in [Custom Components](04-custom-components.md))
   - Use `keboola.component` library for standardized structure
   - Recommended for production transformations and reusable components
   - Automatic I/O mapping, configuration UI, state management, deployment integration

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
