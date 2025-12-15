# Keboola Streamlit App Template

A ready-to-deploy Streamlit data application that connects to Keboola Storage for interactive data exploration, filtering, and visualization.

## What This Template Does

This template provides a fully functional Streamlit app that:

1. Connects to Keboola Storage API
2. Lists and loads tables from your Keboola project
3. Provides interactive data filtering and search
4. Displays data statistics and visualizations
5. Exports filtered data (CSV, JSON)
6. Saves results back to Keboola Storage

## Quick Start

### 1. Install Requirements

**Option A: Using pyproject.toml (recommended - modern Python standard)**
```bash
# Using uv (fastest)
uv sync

# Or using pip
pip install -e .
```

**Option B: Using requirements.txt (traditional)**
```bash
# Using uv
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 2. Set Up Credentials

Create a `.streamlit/secrets.toml` file:

```toml
KEBOOLA_STORAGE_TOKEN = "your-keboola-storage-token"
KEBOOLA_STORAGE_API_URL = "https://connection.keboola.com"
```

Or set environment variables:

```bash
export KEBOOLA_STORAGE_TOKEN="your-token-here"
export KEBOOLA_STORAGE_API_URL="https://connection.keboola.com"
```

To get your token:
1. Go to your Keboola project
2. Navigate to **Users & Settings > API Tokens**
3. Create a new token with appropriate permissions

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Features

### Data Source Selection
- Browse all tables in your Keboola Storage
- See row counts for each table
- Refresh data on demand

### Interactive Filtering
- **Text Search**: Search across all text columns
- **Column Selector**: Show/hide specific columns
- **Numeric Filters**: Filter by value ranges
- **Categorical Filters**: Select specific values
- **Row Limit**: Control how many rows to display

### Statistics & Visualization
- Descriptive statistics for numeric columns
- Value distribution for categorical columns
- Interactive bar charts
- Data type summaries

### Export Options
- Download filtered data as CSV
- Download filtered data as JSON
- Save results back to Keboola Storage

## File Structure

```
streamlit-app/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── .streamlit/
    └── secrets.toml         # Credentials (create this)
```

## Configuration

### Streamlit Configuration

Create `.streamlit/config.toml` for app customization:

```toml
[theme]
primaryColor = "#1f8fff"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
```

### Credentials Management

For production deployment, use Streamlit Cloud secrets:

1. Deploy to Streamlit Cloud
2. Go to App Settings > Secrets
3. Add your `KEBOOLA_STORAGE_TOKEN`

## Deployment

### Deploy to Streamlit Cloud

1. Push code to GitHub repository
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository
5. Set main file path: `templates/streamlit-app/app.py`
6. Add secrets in App Settings
7. Deploy

### Deploy to Keboola Data Apps

1. Create a new Data App in Keboola
2. Upload your code or connect GitHub repository
3. Set `app.py` as the main file
4. Add `requirements.txt`
5. Configure secrets (token is auto-injected in Keboola Data Apps)
6. Deploy

Note: When deploying to Keboola Data Apps, the `KEBOOLA_STORAGE_TOKEN` is automatically provided, so you don't need to configure it manually.

### Deploy with Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv for faster dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:

```bash
docker build -t keboola-streamlit-app .
docker run -p 8501:8501 \
  -e KEBOOLA_STORAGE_TOKEN="your-token" \
  keboola-streamlit-app
```

## Customization

### Add Custom Visualizations

```python
import plotly.express as px

# Add to your app.py
st.subheader("Custom Chart")
fig = px.scatter(df, x='column1', y='column2', color='category')
st.plotly_chart(fig, use_container_width=True)
```

### Add Custom Filtering Logic

```python
# Add custom filter function
def custom_filter(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """Apply custom business logic filters."""
    filtered = df.copy()

    # Example: Filter by date range
    if 'start_date' in criteria and 'end_date' in criteria:
        filtered = filtered[
            (filtered['date'] >= criteria['start_date']) &
            (filtered['date'] <= criteria['end_date'])
        ]

    return filtered

# Use in your app
criteria = {
    'start_date': st.date_input("Start Date"),
    'end_date': st.date_input("End Date")
}
filtered_df = custom_filter(df, criteria)
```

### Add Authentication

```python
import streamlit_authenticator as stauth

# Add to beginning of main()
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Your app code here
    pass
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
```

### Add Data Transformation

```python
# Add transformation section
st.subheader("🔧 Transform Data")

transformation = st.selectbox(
    "Select transformation",
    ["None", "Aggregate by Group", "Pivot Table", "Add Calculated Column"]
)

if transformation == "Aggregate by Group":
    group_col = st.selectbox("Group by column", df.columns)
    agg_col = st.selectbox("Aggregate column", numeric_cols)
    agg_func = st.selectbox("Function", ["sum", "mean", "count", "min", "max"])

    transformed_df = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
    st.dataframe(transformed_df)
```

## Common Use Cases

### Use Case 1: Sales Dashboard

```python
# Customize app.py for sales data
st.title("📊 Sales Dashboard")

# Load sales data
sales_df = load_table_data(client, 'in.c-main.sales')

# Key metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${sales_df['revenue'].sum():,.2f}")
col2.metric("Total Orders", f"{len(sales_df):,}")
col3.metric("Avg Order Value", f"${sales_df['revenue'].mean():.2f}")
col4.metric("Customers", sales_df['customer_id'].nunique())

# Time series chart
sales_by_date = sales_df.groupby('date')['revenue'].sum().reset_index()
st.line_chart(sales_by_date.set_index('date'))
```

### Use Case 2: Data Quality Dashboard

```python
st.title("🔍 Data Quality Monitor")

# Check for issues
issues = []

# Missing values
missing = df.isnull().sum()
if missing.any():
    issues.append(f"Missing values found in {missing[missing > 0].index.tolist()}")

# Duplicates
duplicates = df.duplicated().sum()
if duplicates > 0:
    issues.append(f"{duplicates} duplicate rows found")

# Display issues
if issues:
    st.error("Issues found:")
    for issue in issues:
        st.write(f"- {issue}")
else:
    st.success("✓ No data quality issues detected")
```

### Use Case 3: Customer Segmentation Tool

```python
st.title("👥 Customer Segmentation")

# Load customer data
customers = load_table_data(client, 'in.c-main.customers')

# Segmentation logic
def segment_customer(row):
    ltv = row['lifetime_value']
    if ltv > 10000:
        return 'VIP'
    elif ltv > 1000:
        return 'Regular'
    else:
        return 'New'

customers['segment'] = customers.apply(segment_customer, axis=1)

# Display segments
segment_counts = customers['segment'].value_counts()
st.bar_chart(segment_counts)

# Segment details
selected_segment = st.selectbox("View segment", segment_counts.index)
segment_df = customers[customers['segment'] == selected_segment]
st.dataframe(segment_df)
```

## Best Practices

### 1. Use Caching

Cache expensive operations to improve performance:

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_expensive_data():
    # Expensive computation
    return result
```

### 2. Handle Errors Gracefully

```python
try:
    data = load_table_data(client, table_id)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please check your table ID and permissions")
    st.stop()
```

### 3. Provide User Feedback

```python
with st.spinner("Loading data..."):
    df = load_table_data(client, table_id)

st.success("✓ Data loaded successfully!")
```

### 4. Optimize Data Loading

```python
# Load only required columns
df = load_table_data(client, table_id)
df = df[['id', 'name', 'amount']]  # Select only needed columns

# Sample large datasets
if len(df) > 10000:
    df = df.sample(n=10000)
    st.warning("Large dataset detected. Showing random sample of 10,000 rows.")
```

### 5. Validate User Input

```python
table_name = st.text_input("Table name")

if table_name:
    # Validate format
    if not re.match(r'^[a-z]+\.c-[a-z0-9-]+\.[a-z0-9_-]+$', table_name):
        st.error("Invalid table name format. Use: stage.c-bucket.table")
        st.stop()
```

## Troubleshooting

### Connection Issues

**Problem**: "Failed to initialize Keboola client"

**Solution**:
- Verify your storage token is correct
- Check the API URL matches your Keboola stack
- Ensure token has appropriate permissions

### Performance Issues

**Problem**: App is slow loading data

**Solutions**:
- Enable caching with `@st.cache_data`
- Reduce data volume with input mapping filters
- Load only required columns
- Use data sampling for large datasets

### Memory Issues

**Problem**: App crashes with large datasets

**Solutions**:
- Implement pagination
- Use chunked data loading
- Increase server memory limit in config.toml
- Sample large datasets before display

### Deployment Issues

**Problem**: App doesn't work on Streamlit Cloud

**Solutions**:
- Check secrets are properly configured
- Verify requirements.txt includes all dependencies
- Check Python version compatibility
- Review deployment logs for errors

## Advanced Features

### Add Real-time Data Refresh

```python
# Add auto-refresh
import time

refresh_interval = st.sidebar.slider("Auto-refresh (seconds)", 0, 300, 0)

if refresh_interval > 0:
    st.sidebar.info(f"Auto-refresh enabled: {refresh_interval}s")
    time.sleep(refresh_interval)
    st.rerun()
```

### Add Data Export Scheduling

```python
# Schedule exports
schedule_export = st.sidebar.checkbox("Schedule daily export")

if schedule_export:
    export_time = st.sidebar.time_input("Export time")
    st.sidebar.success(f"Export scheduled for {export_time}")
    # Implement scheduling logic
```

### Add Multi-table Joins

```python
# Join multiple tables
st.subheader("🔗 Join Tables")

table1_id = st.selectbox("First table", table_ids)
table2_id = st.selectbox("Second table", table_ids)

join_key = st.text_input("Join key column")

if st.button("Join Tables"):
    df1 = load_table_data(client, table1_id)
    df2 = load_table_data(client, table2_id)

    joined = pd.merge(df1, df2, on=join_key, how='inner')
    st.dataframe(joined)
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Keboola Storage API](https://developers.keboola.com/integrate/storage/)
- [Keboola Data Apps](https://help.keboola.com/components/data-apps/)
- [Streamlit Cloud](https://streamlit.io/cloud)
- [Example Apps](https://streamlit.io/gallery)

## Support

For issues and questions:

1. Check Streamlit logs for error details
2. Verify Keboola token permissions
3. Review the [Keboola documentation](https://help.keboola.com)
4. Check [Streamlit community forum](https://discuss.streamlit.io/)

## License

This template is provided as-is for use with Keboola Platform and Streamlit.
