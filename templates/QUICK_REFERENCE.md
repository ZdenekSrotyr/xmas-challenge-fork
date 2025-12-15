# Keboola Templates - Quick Reference Card

## Quick Start

```bash
# Use the template creator script
./create-from-template.sh

# Or manually copy
cp -r templates/custom-python my-project
cd my-project
```

## Template Comparison

| Feature | Custom Python | Streamlit App |
|---------|--------------|---------------|
| **Use Case** | Data transformation | Data visualization & exploration |
| **Runs In** | Keboola Transformations | Streamlit Cloud / Keboola Data Apps |
| **Input** | CSV files from Storage | Storage API |
| **Output** | CSV files to Storage | Interactive UI + exports |
| **Best For** | ETL, data processing | Dashboards, data exploration |
| **User Type** | Developers | Analysts + End Users |
| **Complexity** | Simple | Moderate |

## Custom Python Template

### File Paths (Keboola)
```python
# Input tables
/data/in/tables/table_name.csv

# Output tables
/data/out/tables/table_name.csv

# Configuration
/data/config.json
```

### Basic Pattern
```python
# 1. Read input
data = read_input_table('input_table')

# 2. Process
results = process_data(data)

# 3. Write output
write_output_table('output_table', results)
```

### Common Customizations
```python
# Add package to requirements.txt
pandas==2.1.4

# Read config
config = read_config()
threshold = config['parameters']['threshold']

# Multiple inputs
customers = read_input_table('customers')
orders = read_input_table('orders')

# Error handling
try:
    process_data()
except Exception as e:
    print(f"Error: {e}")
    exit(1)
```

## Streamlit App Template

### Setup
```bash
# Install
pip install -r requirements.txt

# Configure
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your token

# Run
streamlit run app.py
```

### Basic Pattern
```python
# 1. Get client
client = get_keboola_client()

# 2. Load data
df = load_table_data(client, 'in.c-main.customers')

# 3. Display
st.dataframe(df)

# 4. Save back (optional)
save_to_storage(client, filtered_df, 'out.c-main.results')
```

### Common Customizations
```python
# Add visualization
import plotly.express as px
fig = px.bar(df, x='category', y='amount')
st.plotly_chart(fig)

# Add custom filter
value = st.slider("Filter by amount", 0, 1000, 500)
filtered = df[df['amount'] > value]

# Cache expensive operations
@st.cache_data(ttl=300)
def load_data():
    return expensive_operation()

# Add user input
user_name = st.text_input("Enter name")
threshold = st.number_input("Threshold", value=100)
```

## Keboola Storage Table IDs

Format: `stage.bucket.table`

### Stages
- `in` - Input bucket
- `out` - Output bucket

### Examples
```
in.c-main.customers
in.c-sales.orders
out.c-main.results
out.c-analytics.summary
```

## Configuration Patterns

### Custom Python - config.json
```json
{
  "parameters": {
    "threshold": 100,
    "debug": false,
    "api_key": "secret-key"
  }
}
```

### Streamlit - secrets.toml
```toml
KEBOOLA_STORAGE_TOKEN = "your-token"
KEBOOLA_STORAGE_API_URL = "https://connection.keboola.com"

[database]
host = "db.example.com"
password = "secret"
```

## Common Data Operations

### Filtering
```python
# Python
filtered = [row for row in data if row['amount'] > 100]

# Pandas
filtered = df[df['amount'] > 100]
```

### Aggregation
```python
# Python
from collections import defaultdict
totals = defaultdict(float)
for row in data:
    totals[row['category']] += float(row['amount'])

# Pandas
totals = df.groupby('category')['amount'].sum()
```

### Joining
```python
# Python (dict-based)
customers_dict = {c['id']: c for c in customers}
for order in orders:
    customer = customers_dict.get(order['customer_id'])

# Pandas
joined = pd.merge(customers, orders, left_on='id', right_on='customer_id')
```

### Sorting
```python
# Python
sorted_data = sorted(data, key=lambda x: x['amount'], reverse=True)

# Pandas
sorted_df = df.sort_values('amount', ascending=False)
```

## Debugging Tips

### Custom Python
```python
# Print to logs
print(f"Processing {len(data)} rows")

# Enable debug mode
if config.get('parameters', {}).get('debug'):
    print(f"Sample row: {data[0]}")

# Check file exists
from pathlib import Path
if Path('/data/in/tables/input.csv').exists():
    print("Input file found")
```

### Streamlit
```python
# Display debug info
st.write("Debug:", variable)

# Show dataframe sample
st.dataframe(df.head())

# Display in sidebar
st.sidebar.write("Debug mode")

# Show errors gracefully
try:
    risky_operation()
except Exception as e:
    st.error(f"Error: {e}")
```

## Performance Tips

### Custom Python
- Process in batches for large datasets
- Use generators for memory efficiency
- Keep requirements minimal
- Exit early on errors

### Streamlit
- Use `@st.cache_data` for expensive operations
- Limit rows displayed (use pagination)
- Load only needed columns
- Sample large datasets
- Set appropriate TTL on cache

## Common Errors & Solutions

### FileNotFoundError
```python
# Check input mapping in Keboola UI
# Verify file name matches exactly
print(os.listdir('/data/in/tables'))
```

### Module not found
```python
# Add to requirements.txt
package-name==version
```

### Token/Auth errors
```python
# Verify token has correct permissions
# Check API URL matches your stack
# Ensure token not expired
```

### Memory errors
```python
# Process in chunks
for chunk in pd.read_csv('file.csv', chunksize=1000):
    process(chunk)

# Or sample data
df = df.sample(n=10000)
```

## Testing Locally

### Custom Python
```bash
# Create test structure
mkdir -p /data/in/tables /data/out/tables

# Create test input
echo "id,name,amount" > /data/in/tables/input_table.csv
echo "1,Test,100" >> /data/in/tables/input_table.csv

# Create test config
echo '{"parameters": {"threshold": 50}}' > /data/config.json

# Run script
python main.py

# Check output
cat /data/out/tables/output_table.csv
```

### Streamlit App
```bash
# Set test token
export KEBOOLA_STORAGE_TOKEN="test-token"

# Run app
streamlit run app.py

# Or use secrets file
echo 'KEBOOLA_STORAGE_TOKEN = "token"' > .streamlit/secrets.toml
streamlit run app.py
```

## Deployment Checklist

### Custom Python
- [ ] Customize process_data() function
- [ ] Update requirements.txt
- [ ] Test with sample data locally
- [ ] Configure input mapping in Keboola
- [ ] Configure output mapping in Keboola
- [ ] Add parameters if needed
- [ ] Run transformation in Keboola
- [ ] Check logs for errors
- [ ] Verify output tables

### Streamlit App
- [ ] Install dependencies
- [ ] Configure secrets/token
- [ ] Test locally
- [ ] Update app.py with customizations
- [ ] Choose deployment target (Streamlit Cloud or Keboola Data Apps)
- [ ] Push to Git (if using Streamlit Cloud)
- [ ] Configure secrets in deployment platform
- [ ] Deploy and test
- [ ] Share URL with users

## Getting Help

### Documentation
- Templates: `templates/README.md`
- Custom Python: `templates/custom-python/README.md`
- Streamlit: `templates/streamlit-app/README.md`

### Keboola Resources
- Help Center: https://help.keboola.com
- Developers: https://developers.keboola.com
- Storage API: https://developers.keboola.com/integrate/storage/

### External Resources
- Python: https://docs.python.org/3/
- Pandas: https://pandas.pydata.org/docs/
- Streamlit: https://docs.streamlit.io/

## Keyboard Shortcuts

### Streamlit App
- `R` - Rerun app
- `C` - Clear cache
- `Ctrl+C` - Stop server
- `Ctrl+Shift+R` - Force reload

## Best Practices Summary

1. **Start simple** - Use template as-is first, then customize
2. **Test locally** - Always test before deploying
3. **Use version control** - Track changes with git
4. **Document changes** - Add comments for customizations
5. **Handle errors** - Add try/catch blocks
6. **Log progress** - Use print statements
7. **Keep requirements minimal** - Only add packages you need
8. **Use type hints** - Makes code more maintainable
9. **Cache when possible** - Improves performance
10. **Ask for help** - Check docs or community forums

---

**Quick Commands**

```bash
# Create new project
./create-from-template.sh custom-python my-transform

# Test Custom Python
python main.py

# Run Streamlit
streamlit run app.py

# Install requirements
pip install -r requirements.txt

# Check syntax
python -m py_compile main.py
```

---

For detailed documentation, see individual template README files.
