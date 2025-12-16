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

**When to Use What**:

```python
# Use WORKSPACE when:
# - Running inside Data App (production)
# - Running transformation
# - Direct SQL queries needed
if 'KBC_PROJECT_ID' in os.environ:
    conn = st.connection('snowflake', type='snowflake')
    query = f'SELECT * FROM "{os.environ["KBC_PROJECT_ID"]}"."{os.environ["in.c-main"]}"."customers"'
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

## Webhooks

Webhooks allow you to receive real-time notifications about events in your Keboola project, such as job completions, errors, and configuration changes.

### Setting Up Webhooks

Webhooks are configured at the project level via the Storage API:

```python
import requests
import os

stack_url = os.environ.get("KEBOOLA_STACK_URL", "connection.keboola.com")
token = os.environ["KEBOOLA_TOKEN"]

# Create a webhook
response = requests.post(
    f"https://{stack_url}/v2/storage/webhooks",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://your-app.com/webhook",
        "events": [
            "storage.jobSucceeded",
            "storage.jobFailed",
            "storage.tableCreated"
        ],
        "name": "My Webhook"
    }
)
response.raise_for_status()

webhook = response.json()
print(f"Webhook created with ID: {webhook['id']}")
```

### Event Types

Common webhook event types:

**Job Events**:
- `storage.jobSucceeded` - Job completed successfully
- `storage.jobFailed` - Job failed with error
- `storage.jobProcessing` - Job started processing
- `storage.jobWaiting` - Job is queued

**Table Events**:
- `storage.tableCreated` - New table created
- `storage.tableImported` - Data imported to table
- `storage.tableDeleted` - Table deleted

**Configuration Events**:
- `orchestration.jobSucceeded` - Orchestration completed
- `orchestration.jobFailed` - Orchestration failed

### Webhook Payload Format

Webhook requests are POST requests with JSON payload:

```json
{
  "event": "storage.jobSucceeded",
  "data": {
    "id": "12345678",
    "runId": "12345678.87654321",
    "project": {
      "id": "6789",
      "name": "My Project"
    },
    "component": "keboola.ex-db-mysql",
    "configurationId": "123",
    "status": "success",
    "startTime": "2024-01-15T10:30:00+0000",
    "endTime": "2024-01-15T10:35:00+0000",
    "durationSeconds": 300
  },
  "createdTime": "2024-01-15T10:35:01+0000"
}
```

### Webhook Security (Signature Verification)

All webhook requests include an `X-Kbc-Signature` header with HMAC-SHA256 signature for verification:

```python
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_token"  # From webhook creation response

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Get signature from header
    received_signature = request.headers.get('X-Kbc-Signature')
    if not received_signature:
        abort(401, "Missing signature")
    
    # Compute expected signature
    payload = request.get_data()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Verify signature
    if not hmac.compare_digest(received_signature, expected_signature):
        abort(401, "Invalid signature")
    
    # Process webhook
    event_data = request.json
    print(f"Received event: {event_data['event']}")
    
    if event_data['event'] == 'storage.jobFailed':
        # Handle job failure
        job_id = event_data['data']['id']
        send_alert(f"Job {job_id} failed")
    
    return {"status": "ok"}, 200
```

### Managing Webhooks

**List webhooks**:
```python
response = requests.get(
    f"https://{stack_url}/v2/storage/webhooks",
    headers={"X-StorageApi-Token": token}
)
webhooks = response.json()
```

**Update webhook**:
```python
webhook_id = "123"
response = requests.put(
    f"https://{stack_url}/v2/storage/webhooks/{webhook_id}",
    headers={
        "X-StorageApi-Token": token,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://your-app.com/new-webhook",
        "events": ["storage.jobSucceeded"]
    }
)
```

**Delete webhook**:
```python
webhook_id = "123"
response = requests.delete(
    f"https://{stack_url}/v2/storage/webhooks/{webhook_id}",
    headers={"X-StorageApi-Token": token}
)
```

### Best Practices

**DO**:
- Always verify webhook signatures to prevent spoofing
- Use HTTPS endpoints for webhook URLs
- Respond quickly (within 30 seconds) to avoid timeouts
- Process webhooks asynchronously if heavy processing is needed
- Store webhook secrets securely (environment variables, secret managers)
- Log webhook events for debugging
- Handle duplicate events idempotently

**DON'T**:
- Skip signature verification
- Use HTTP (unencrypted) webhook endpoints
- Perform long-running operations in webhook handler
- Hardcode webhook secrets in code
- Assume webhooks arrive in order
- Ignore retry logic for failed deliveries

### Webhook Retries

Keboola automatically retries failed webhook deliveries:
- Retries up to 3 times with exponential backoff
- Considers 2xx status codes as success
- Timeout after 30 seconds per attempt

### Testing Webhooks Locally

Use tunneling tools to test webhooks during development:

```bash
# Using ngrok
ngrok http 5000

# Use the ngrok URL for webhook configuration
# https://abc123.ngrok.io/webhook
```
