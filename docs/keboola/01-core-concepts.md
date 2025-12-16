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
- **Transformations**: Process and modify data (SQL, Python, R)
- **Writers**: Send data to external destinations
- **Custom Components**: User-built components deployed via Developer Portal

Components can be used in two ways:
1. **Pre-built components**: Available in Keboola Component Library
2. **Custom components**: Your own Python/R code packaged as Docker containers

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
