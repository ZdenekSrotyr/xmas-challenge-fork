# Getting Started with Keboola Templates

Welcome! This guide will get you started with the Keboola development templates in 5 minutes.

## What Are These Templates?

Think of these as **starter kits** for common Keboola development tasks:

1. **Custom Python**: Transform data in Keboola with Python
2. **Streamlit App**: Build interactive data applications

Both are production-ready, tested, and documented.

## Quick Decision Guide

### Use Custom Python Template When:
- ✅ You need to transform data in Keboola
- ✅ You want to read from Storage, process, and write back
- ✅ You need custom business logic
- ✅ You're comfortable with Python

### Use Streamlit App Template When:
- ✅ You want an interactive dashboard
- ✅ You need to explore data visually
- ✅ You want to share data with non-technical users
- ✅ You need filtering and export capabilities

## 5-Minute Quick Start

### Option 1: Custom Python (Data Transformation)

```bash
# Step 1: Copy template
cd templates
cp -r custom-python my-transformation
cd my-transformation

# Step 2: Look at the code
cat main.py  # See what it does

# Step 3: Test it locally (optional)
# Create test data structure
mkdir -p /data/in/tables /data/out/tables

# Create sample input
cat > /data/in/tables/input_table.csv << EOF
id,name,amount
1,Customer A,150
2,Customer B,75
3,Customer C,250
EOF

# Create config
echo '{"parameters": {"threshold": 100}}' > /data/config.json

# Run it!
python main.py

# Step 4: Customize for your needs
# Edit the process_data() function in main.py

# Step 5: Deploy to Keboola
# 1. Create new Custom Python transformation in Keboola
# 2. Paste main.py content
# 3. Set up input/output mapping
# 4. Run it!
```

### Option 2: Streamlit App (Data Dashboard)

```bash
# Step 1: Copy template
cd templates
cp -r streamlit-app my-dashboard
cd my-dashboard

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Set up credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit secrets.toml and add your Keboola token:
# KEBOOLA_STORAGE_TOKEN = "your-token-here"
# Get token from: Keboola > Users & Settings > API Tokens

# Step 4: Run it!
streamlit run app.py

# Your browser will open automatically
# Try browsing your tables, filtering data, exporting!

# Step 5: Customize
# Edit app.py to add your own features
```

## Understanding the Structure

### Custom Python Template

```
custom-python/
├── main.py              ← Main script (start here!)
├── requirements.txt     ← Add Python packages here
└── README.md           ← Detailed documentation
```

**Key functions in main.py**:
- `read_input_table()` - Read data from Keboola Storage
- `process_data()` - **CUSTOMIZE THIS** with your logic
- `write_output_table()` - Write results back to Storage
- `main()` - Orchestrates everything

### Streamlit App Template

```
streamlit-app/
├── app.py                ← Main application (start here!)
├── requirements.txt      ← Dependencies
├── .streamlit/
│   ├── config.toml      ← App configuration
│   └── secrets.toml     ← Your credentials (create this)
└── README.md            ← Detailed documentation
```

**Key functions in app.py**:
- `get_keboola_client()` - Connect to Keboola
- `load_table_data()` - Load table from Storage
- `save_to_storage()` - Save filtered data back
- `main()` - The app UI

## First Customization Examples

### Custom Python: Change the Processing Logic

Find this function in `main.py`:

```python
def process_data(input_data: list[dict], threshold: int = 100) -> list[dict]:
    """
    Example data processing function.

    Replace this with your actual business logic.
    """
    results = []

    for row in input_data:
        # YOUR CUSTOM LOGIC HERE
        # Example: Filter and transform
        amount = float(row.get('amount', 0))

        if amount >= threshold:
            results.append({
                'id': row.get('id'),
                'name': row.get('name'),
                'amount': amount,
                # Add your calculated fields
            })

    return results
```

**What to change**:
1. The filtering logic (`if amount >= threshold`)
2. The output fields (what goes in `results.append()`)
3. Add calculations, lookups, enrichment, etc.

### Streamlit App: Add a Custom Chart

Add this to `app.py` after loading data:

```python
# After: df = load_table_data(client, selected_table_id)

import plotly.express as px

st.subheader("📊 Amount Distribution")

# Create a chart
fig = px.histogram(df, x='amount', nbins=20)
st.plotly_chart(fig, use_container_width=True)
```

Uncomment in `requirements.txt`:
```txt
plotly==5.18.0
```

## Common First-Time Questions

### Q: Do I need to modify these templates?
**A**: No! They work as-is. But you'll want to customize the business logic for your use case.

### Q: Can I use these in production?
**A**: Yes! They're production-ready with error handling, logging, and best practices.

### Q: What if I break something?
**A**: Just copy the template again. That's the beauty of templates!

### Q: Do I need to know Python well?
**A**: Basic Python knowledge helps. The templates show you the patterns - you fill in the logic.

### Q: Where do I get a Keboola token?
**A**:
1. Go to your Keboola project
2. Users & Settings > API Tokens
3. Create new token
4. Give it appropriate permissions (read Storage for Streamlit, read/write for Custom Python)

### Q: How do I test locally?
**A**: See the "Test Locally" sections in each template's README.md

## Next Steps

### After You're Comfortable

1. **Read the full documentation**:
   - `templates/README.md` - Overview of all templates
   - `templates/custom-python/README.md` - Deep dive on Custom Python
   - `templates/streamlit-app/README.md` - Deep dive on Streamlit
   - `templates/QUICK_REFERENCE.md` - Quick lookup guide

2. **Explore the examples**:
   - Each README has 3+ complete examples
   - Customer segmentation
   - Sales reporting
   - Data quality checks
   - And more!

3. **Add advanced features**:
   - Multiple input tables
   - External API calls
   - Data validation
   - Custom visualizations
   - Authentication

4. **Deploy to production**:
   - Keboola Transformations (Custom Python)
   - Streamlit Cloud (free tier)
   - Keboola Data Apps
   - Docker containers

## Using the Template Creator Script

Instead of manually copying, use our helper script:

```bash
cd templates

# Interactive mode - it will guide you
./create-from-template.sh

# Or command line mode
./create-from-template.sh custom-python my-project
./create-from-template.sh streamlit-app my-dashboard
```

The script will:
- Ask which template you want
- Ask where to create it
- Copy all files
- Show you next steps

## Getting Help

### Start Here
1. **README files**: Each template has comprehensive documentation
2. **Quick Reference**: `templates/QUICK_REFERENCE.md`
3. **Examples**: Look in the README files for complete examples

### If You're Stuck
1. **Check the troubleshooting section** in the template README
2. **Look at the error message** - they're designed to be helpful
3. **Enable debug mode** (Custom Python) or use `st.write()` (Streamlit) to see what's happening

### External Resources
- [Keboola Help Center](https://help.keboola.com)
- [Keboola Developer Docs](https://developers.keboola.com)
- [Python Documentation](https://docs.python.org/3/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## Tips for Success

1. **Start simple**: Use the template as-is first, then customize
2. **Test locally**: Don't develop in production
3. **Read the comments**: The code is heavily documented
4. **Use the examples**: The READMEs have real-world examples
5. **Ask questions**: Check documentation or community forums

## What's Included

Each template includes:

- ✅ **Working code** - Copy-paste-run ready
- ✅ **Comprehensive documentation** - 400+ lines each
- ✅ **Real examples** - Not toy code
- ✅ **Error handling** - Production-ready
- ✅ **Best practices** - Modern Python patterns
- ✅ **Test workflows** - Automated validation
- ✅ **Configuration examples** - All you need

## Your First Win

Try this now:

```bash
# 1. Go to templates directory
cd templates/streamlit-app

# 2. Install requirements
pip install -r requirements.txt

# 3. Set a dummy token (to see the UI)
mkdir -p .streamlit
echo 'KEBOOLA_STORAGE_TOKEN = "test"' > .streamlit/secrets.toml

# 4. Run it
streamlit run app.py

# You'll see the UI even without real data!
# It will show an error about the token, but you can see the interface
```

## Success Stories to Inspire You

**From this template, you can build**:

- Customer segmentation dashboards
- Sales analytics tools
- Data quality monitors
- Inventory tracking apps
- Marketing analytics dashboards
- Financial reporting tools
- Operational dashboards
- And much more!

## The Path Forward

```
Start with template
       ↓
Understand how it works (5 minutes)
       ↓
Customize for your use case (30 minutes)
       ↓
Test with real data (15 minutes)
       ↓
Deploy to production (10 minutes)
       ↓
Share with team / users
       ↓
Iterate and improve
```

**Total time to first deployment: ~1 hour**

(Compare that to building from scratch: days or weeks!)

## Ready?

Pick a template and dive in:

- **Want to transform data?** → Start with `custom-python/`
- **Want to visualize data?** → Start with `streamlit-app/`
- **Not sure?** → Try both! They're quick to set up

**Pro tip**: Start with Streamlit app - it's more visual and you'll see results immediately!

---

**You've got this!** The templates are designed to make you successful. Follow the steps, read the docs, and you'll be building production-grade Keboola applications in no time.

Questions? Check the README files - they're incredibly comprehensive.

Happy building! 🚀
