# Data App Development

## Overview

Keboola Data Apps are Streamlit applications that run directly in the Keboola platform, providing interactive dashboards and analytics tools. They connect to Keboola Storage and can query data from workspace tables.

## Key Concepts

### What are Data Apps?

Data Apps are containerized Streamlit applications that:
- Run inside Keboola's infrastructure
- Have direct access to project data via workspace
- Support interactive filtering, visualization, and exploration
- Can be shared with team members
- Auto-scale based on usage

### Architecture Pattern: SQL-First

**Core Principle**: Push computation to the database, never load large datasets into Python.

Why?
- Keboola workspaces (Snowflake, Redshift, BigQuery) are optimized for queries
- Loading data into Streamlit doesn't scale
- SQL aggregation is 10-100x faster than pandas

## Project Structure

```
my-dataapp/
├── streamlit_app.py          # Main app entry point with sidebar
├── pages/
│   ├── 01_Overview.py        # First page
│   ├── 02_Analytics.py       # Second page
│   └── 03_Details.py         # Third page
├── utils/
│   ├── data_loader.py        # Centralized data access
│   └── config.py             # Environment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

## Environment Setup

### Local Development

Data apps must work in two environments with **different contexts**:

1. **Local Development (Storage API / Project Context)**: 
   - Uses Storage API token for authentication
   - References tables as `in.c-bucket.table`
   - Exports data via REST API
   - No workspace ID involved

2. **Production (Workspace Context)**: 
   - Uses workspace database connection
   - References tables as `"PROJECT_ID"."in.c-bucket"."table"`
   - Queries data via SQL
   - Requires workspace environment variables

**Why Two Contexts?**

In production, Data Apps run inside a **Keboola workspace** (Snowflake/Redshift instance) where your project data is mirrored. This provides:
- Direct SQL access (fast queries)
- No API rate limits
- Native database features

During local development, you don't have workspace access, so you use the **Storage API** (REST) to export data.

**Environment Variables by Context**:

```python
# WORKSPACE CONTEXT (Production)
# Automatically set by Keboola platform:
KBC_PROJECT_ID=6789           # Your project ID (used in table references)
KBC_BUCKET_ID=in.c-main       # Default bucket for app
KBC_TABLE_NAME=customers      # Default table for app

# STORAGE API CONTEXT (Local)
# You must set manually:
KEBOOLA_TOKEN=your-token                        # Storage API token
KEBOOLA_STACK_URL=connection.keboola.com       # Your stack URL
```

```python
# utils/config.py
import os
import streamlit as st

def get_connection_mode():
    """Detect if running locally or in Keboola."""
    return 'workspace' if 'KBC_PROJECT_ID' in os.environ else 'local'

def get_storage_token():
    """Get Storage API token from environment."""
    return os.environ.get('KEBOOLA_TOKEN')

def get_stack_url():
    """Get Keboola stack URL."""
    return os.environ.get('KEBOOLA_STACK_URL', 'connection.keboola.com')
```

### Connection Setup

```python
# utils/data_loader.py
import os
import streamlit as st
from utils.config import get_connection_mode

@st.cache_resource
def get_connection():
    """Get database connection based on environment."""
    mode = get_connection_mode()

    if mode == 'workspace':
        # Running in Keboola - use workspace connection
        return st.connection('snowflake', type='snowflake')
    else:
        # Local development - use Storage API
        return None  # Implement Storage API wrapper

def get_table_name():
    """Get fully qualified table name."""
    mode = get_connection_mode()

    if mode == 'workspace':
        # In workspace: database.schema.table
        return f'"{os.environ["KBC_PROJECT_ID"]}"."{os.environ["KBC_BUCKET_ID"]}"."{os.environ["KBC_TABLE_NAME"]}"'
    else:
        # Local: bucket.table
        return 'in.c-analysis.usage_data'
```

## SQL-First Design Pattern

### Good Pattern: Aggregate in Database

```python
@st.cache_data(ttl=300)
def get_summary_metrics(where_clause: str = ""):
    query = f'''
        SELECT
            COUNT(*) as total_count,
            COUNT(DISTINCT "user_id") as unique_users,
            AVG("session_duration") as avg_duration,
            SUM("revenue") as total_revenue
        FROM {get_table_name()}
        WHERE "date" >= CURRENT_DATE - INTERVAL '90 days'
            {f"AND {where_clause}" if where_clause else ""}
    '''
    return execute_query(query)
```

### Bad Pattern: Load All Data

```python
# DON'T DO THIS
df = execute_query(f"SELECT * FROM {get_table_name()}")
result = df.groupby('category').agg({'value': 'mean'})
```

## Global Filter Pattern

Global filters allow users to filter all pages from one control in the sidebar.

### Step 1: Create Filter Function

```python
# utils/data_loader.py
import streamlit as st

def get_user_type_filter_clause():
    """Get SQL WHERE clause for user type filter."""
    # Initialize session state with default
    if 'user_filter' not in st.session_state:
        st.session_state.user_filter = 'external'

    # Return appropriate SQL condition
    if st.session_state.user_filter == 'external':
        return '"user_type" = \'External User\''
    elif st.session_state.user_filter == 'internal':
        return '"user_type" = \'Keboola User\''
    return ''  # 'all' - no filter
```

### Step 2: Add UI Control

```python
# streamlit_app.py (sidebar)
import streamlit as st
from utils.data_loader import get_user_type_filter_clause

st.set_page_config(page_title="My Dashboard", layout="wide")

# Initialize session state
if 'user_filter' not in st.session_state:
    st.session_state.user_filter = 'external'

# Sidebar filter
st.sidebar.header("Filters")
user_option = st.sidebar.radio(
    "User Type:",
    options=['external', 'internal', 'all'],
    index=['external', 'internal', 'all'].index(st.session_state.user_filter)
)

# Update session state and trigger rerun if changed
if user_option != st.session_state.user_filter:
    st.session_state.user_filter = user_option
    st.rerun()
```

### Step 3: Use Filter in Pages

```python
# pages/01_Overview.py
import streamlit as st
from utils.data_loader import get_user_type_filter_clause, execute_query

# Build WHERE clause
where_parts = ['"status" = \'active\'']  # Base filter
user_filter = get_user_type_filter_clause()
if user_filter:
    where_parts.append(user_filter)
where_clause = ' AND '.join(where_parts)

# Use in query
@st.cache_data(ttl=300)
def get_page_data():
    query = f'''
        SELECT "date", COUNT(*) as count
        FROM {get_table_name()}
        WHERE {where_clause}
        GROUP BY "date"
        ORDER BY "date"
    '''
    return execute_query(query)

df = get_page_data()
st.line_chart(df, x='date', y='count')
```

## Query Execution

### Basic Query Function

```python
# utils/data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=300)
def execute_query(sql: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    conn = get_connection()

    try:
        df = conn.query(sql)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
```

### SQL Best Practices

**Always quote identifiers**:
```sql
-- CORRECT
SELECT "user_id", "revenue" FROM "my_table"

-- WRONG (fails with reserved keywords or mixed case)
SELECT user_id, revenue FROM my_table
```

**Use parameterized WHERE clauses**:
```python
def get_date_filter_clause(start_date, end_date):
    """Generate date range filter."""
    return f'"date" BETWEEN \'{start_date}\' AND \'{end_date}\''
```

## Caching Strategy

### Cache Database Connections

```python
@st.cache_resource
def get_connection():
    """Cache connection object (doesn't change)."""
    return st.connection('snowflake', type='snowflake')
```

### Cache Query Results

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_metrics(where_clause: str):
    """Cache query results (data can change)."""
    query = f"SELECT COUNT(*) FROM {get_table_name()} WHERE {where_clause}"
    return execute_query(query)
```

### TTL Guidelines

- **Static reference data**: `ttl=3600` (1 hour)
- **Dashboard metrics**: `ttl=300` (5 minutes)
- **Real-time data**: `ttl=60` (1 minute)
- **User-specific data**: No cache or very short TTL

## Session State Management

Streamlit reruns the entire script on every interaction. Use session state to persist values.

### Initialize Before Use

```python
# Always initialize session state before creating widgets
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = 'all'

# Now create widget
category = st.selectbox(
    "Category",
    options=['all', 'sales', 'marketing'],
    index=['all', 'sales', 'marketing'].index(st.session_state.selected_category)
)

# Update session state if changed
if category != st.session_state.selected_category:
    st.session_state.selected_category = category
    st.rerun()
```

## Error Handling

### Handle Empty Results

```python
df = get_page_data()

if df.empty:
    st.warning("No data available for the selected filters.")
else:
    st.line_chart(df, x='date', y='count')
```

### Catch Query Errors

```python
@st.cache_data(ttl=300)
def execute_query(sql: str):
    try:
        conn = get_connection()
        return conn.query(sql)
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()
```

## Common Patterns

### Metric Cards

```python
@st.cache_data(ttl=300)
def get_kpi_metrics():
    query = f'''
        SELECT
            COUNT(*) as total_users,
            SUM("revenue") as total_revenue,
            AVG("session_duration") as avg_duration
        FROM {get_table_name()}
        WHERE "date" >= CURRENT_DATE - INTERVAL '30 days'
    '''
    return execute_query(query).iloc[0]

metrics = get_kpi_metrics()

col1, col2, col3 = st.columns(3)
col1.metric("Total Users", f"{metrics['total_users']:,}")
col2.metric("Revenue", f"${metrics['total_revenue']:,.2f}")
col3.metric("Avg Duration", f"{metrics['avg_duration']:.1f}s")
```

### Date Range Filter

```python
import datetime

col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = col2.date_input("End Date", datetime.date.today())

where_clause = f'"date" BETWEEN \'{start_date}\' AND \'{end_date}\''
```

### Dynamic Dropdown

```python
@st.cache_data(ttl=3600)
def get_categories():
    query = f'SELECT DISTINCT "category" FROM {get_table_name()} ORDER BY "category"'
    return execute_query(query)['category'].tolist()

categories = get_categories()
selected = st.selectbox("Category", options=['All'] + categories)
```

## Variable Naming Conventions

### Avoid Naming Conflicts

**Problem**: Using same variable name for SQL clause and UI widget
```python
# DON'T DO THIS
user_filter = get_user_filter_clause()  # SQL string
user_filter = st.radio("User Type", ...)  # UI widget - overwrites SQL!
```

**Solution**: Use descriptive, unique names
```python
# DO THIS
user_filter_sql = get_user_filter_clause()  # SQL string
user_filter_option = st.radio("User Type", ...)  # UI widget
```

### Session State Keys

Use consistent, descriptive keys:
```python
# Good
st.session_state.user_type_filter = 'external'
st.session_state.selected_date_range = (start, end)
st.session_state.page_number = 1

# Bad (ambiguous)
st.session_state.filter = 'external'
st.session_state.data = (start, end)
st.session_state.page = 1
```

## Deployment

### Requirements File

```txt
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
snowflake-connector-python>=3.0.0
plotly>=5.17.0
```

### Environment Variables

Required in Keboola deployment:
- `KBC_PROJECT_ID` - Automatically set by platform
- `KBC_BUCKET_ID` - Automatically set by platform
- `KEBOOLA_TOKEN` - Set in Data App configuration
- `KEBOOLA_STACK_URL` - Set in Data App configuration

### Testing Before Deployment

```bash
# Local testing
export KEBOOLA_TOKEN=your_token
export KEBOOLA_STACK_URL=connection.keboola.com
streamlit run streamlit_app.py
```

## Best Practices

### DO:

- Always validate data schemas before writing code
- Push computation to database - aggregate in SQL, not Python
- Use fully qualified table names from `get_table_name()`
- Quote all identifiers in SQL (`"column_name"`)
- Cache all queries with `@st.cache_data(ttl=300)`
- Centralize data access in `utils/data_loader.py`
- Initialize session state with defaults before UI controls
- Use unique, descriptive variable names
- Test visually before deploying
- Handle empty DataFrames gracefully
- Support both local and production environments

### DON'T:

- Skip data validation - always check schemas first
- Load large datasets into Python - aggregate in database
- Hardcode table names - use `get_table_name()` function
- Use same variable name twice (SQL clause and UI widget)
- Forget session state initialization before creating widgets
- Assume columns exist - validate first
- Use unquoted SQL identifiers
- Skip error handling for empty query results
- Deploy without local testing

## Visual Verification Workflow

Before deploying, test your app:

1. **Start local server**: `streamlit run streamlit_app.py`
2. **Open in browser**: `http://localhost:8501`
3. **Test all interactions**:
   - Click through all pages
   - Try all filter combinations
   - Verify metrics update correctly
   - Check for error messages
4. **Capture screenshots** of working features
5. **Deploy with confidence**

## Common Issues

### "KeyError: 'column_name'"

**Cause**: Column doesn't exist or wrong name
**Solution**: Validate schema before querying:
```python
# Check available columns first
query = f'SELECT * FROM {get_table_name()} LIMIT 1'
df = execute_query(query)
print(df.columns)  # See actual column names
```

### Filter Not Working

**Cause**: Filter SQL not included in WHERE clause
**Solution**: Always build WHERE clause systematically:
```python
where_parts = []
if base_filter := get_base_filter():
    where_parts.append(base_filter)
if user_filter := get_user_filter_clause():
    where_parts.append(user_filter)
where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
```

### Session State Not Persisting

**Cause**: Not initializing before widget creation
**Solution**: Initialize before use:
```python
if 'my_value' not in st.session_state:
    st.session_state.my_value = default_value

widget = st.text_input("Label", value=st.session_state.my_value)
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Keboola Data Apps Guide](https://help.keboola.com/components/data-apps/)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference.html)

## Table Name Helper

```python
def get_table_name():
    """Get fully qualified table name for current context.
    
    Returns:
        Workspace context: '"PROJECT_ID"."BUCKET_ID"."TABLE_NAME"' (quoted, SQL-safe)
        Storage API context: 'BUCKET_ID.TABLE_NAME' (for API endpoints)
    
    Context difference:
    - Workspace uses PROJECT_ID as database name (Snowflake schema)
    - Storage API uses bucket.table format (no project ID)
    """
    mode = get_connection_mode()

    if mode == 'workspace':
        # WORKSPACE CONTEXT: Running in Keboola (has workspace access)
        # Use PROJECT_ID as database qualifier for Snowflake queries
        project_id = os.environ['KBC_PROJECT_ID']  # e.g., "6789"
        bucket = os.environ.get('KBC_BUCKET_ID', 'in.c-analysis')  # e.g., "in.c-main"
        table = os.environ.get('KBC_TABLE_NAME', 'usage_data')  # e.g., "customers"
        
        # Return: "6789"."in.c-main"."customers"
        return f'"{project_id}"."{bucket}"."{table}"'
    else:
        # STORAGE API CONTEXT: Running locally (no workspace)
        # Use bucket.table format for Storage API endpoints
        bucket = 'in.c-analysis'
        table = 'usage_data'
        
        # Return: in.c-analysis.usage_data
        return f'{bucket}.{table}'
```
