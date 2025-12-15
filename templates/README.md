# Keboola Development Templates

Quick-start templates for common Keboola development scenarios. These templates are production-ready, well-documented, and designed to get you up and running quickly.

## Available Templates

### 1. Custom Python Script

**Location**: `templates/custom-python/`

**What it does**: Complete template for Keboola Custom Python transformations with input/output mapping, configuration handling, and error management.

**Use when**:
- You need to process data with Python in Keboola
- You want to read from Storage, transform, and write back
- You need custom business logic that SQL can't handle

**Features**:
- Read/write from Keboola Storage tables
- Configuration parameter handling
- Comprehensive error handling
- Multiple processing patterns (filter, aggregate, enrich)
- Full inline documentation

**Quick Start**:
```bash
# Copy to your project
cp templates/custom-python/main.py your-transformation/

# Customize the process_data() function
# Configure input/output mapping in Keboola UI
# Run your transformation
```

[Full Documentation](custom-python/README.md)

---

### 2. Streamlit Data App

**Location**: `templates/streamlit-app/`

**What it does**: Interactive Streamlit application that connects to Keboola Storage for data exploration, filtering, and visualization.

**Use when**:
- You need an interactive data viewer/dashboard
- You want to share data with non-technical users
- You need to explore and filter data visually
- You want to deploy a data app quickly

**Features**:
- Connect to Keboola Storage API
- Interactive table browser
- Advanced filtering (text search, ranges, categories)
- Export data (CSV, JSON, back to Storage)
- Statistics and visualizations
- Ready for Streamlit Cloud or Keboola Data Apps

**Quick Start**:
```bash
# Install dependencies
cd templates/streamlit-app
uv sync  # modern way using pyproject.toml
# or: uv pip install -r requirements.txt  # traditional way
# or: pip install -r requirements.txt  # using pip

# Set up credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your token

# Run the app
streamlit run app.py
```

[Full Documentation](streamlit-app/README.md)

---

## How to Use These Templates

### Method 1: Copy and Customize

The simplest approach - copy the template and modify for your needs:

```bash
# Copy template
cp -r templates/custom-python my-transformation

# Customize
cd my-transformation
# Edit main.py with your logic
# Update requirements.txt if needed
```

### Method 2: Use as Reference

Keep templates as reference while building your own:

```bash
# Open template for reference
cat templates/custom-python/main.py

# Use patterns and functions in your code
# Adapt to your specific requirements
```

### Method 3: Integrate into Your Workflow

For teams, add templates to your development workflow:

```bash
# Create project-specific templates directory
mkdir my-project/templates
cp -r templates/* my-project/templates/

# Add team-specific customizations
# Share with team via Git
```

## Template Structure

Each template follows a consistent structure:

```
template-name/
├── README.md              # Comprehensive documentation
├── main-file.py          # Main application code
├── requirements.txt      # Python dependencies
├── .github/
│   └── workflows/
│       └── test-template.yml  # Automated testing
└── Additional config files
```

## Customization Guide

### Common Customizations

#### 1. Change Data Processing Logic

**Custom Python**:
```python
# Edit the process_data() function in main.py
def process_data(input_data: list[dict], threshold: int) -> list[dict]:
    # Your custom logic here
    return processed_results
```

**Streamlit App**:
```python
# Add custom transformations in app.py
def custom_transform(df: pd.DataFrame) -> pd.DataFrame:
    # Your transformation logic
    return transformed_df
```

#### 2. Add External API Calls

```python
# Add to requirements.txt
# requests==2.31.0

# Use in your code
import requests

def fetch_external_data(api_key: str) -> dict:
    response = requests.get(
        'https://api.example.com/data',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    return response.json()
```

#### 3. Add Data Validation

```python
from pydantic import BaseModel, ValidationError

class CustomerRecord(BaseModel):
    id: str
    name: str
    amount: float

def validate_row(row: dict) -> CustomerRecord | None:
    try:
        return CustomerRecord(**row)
    except ValidationError as e:
        print(f"Invalid row: {e}")
        return None
```

#### 4. Add Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in your code
logger.info("Processing started")
logger.error(f"Failed to process row: {row}")
```

### Environment-Specific Customization

#### Development vs Production

```python
import os

ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'development':
    DEBUG = True
    CACHE_TTL = 60
else:
    DEBUG = False
    CACHE_TTL = 300
```

#### Multi-tenant Configuration

```python
# Read tenant-specific config
config = read_config()
tenant_id = config.get('parameters', {}).get('tenant_id')

# Load tenant-specific settings
tenant_settings = load_tenant_settings(tenant_id)
```

## Best Practices

### 1. Keep Templates Updated

Templates are starting points, not static code:

- Update dependencies regularly
- Add new patterns as you discover them
- Share improvements with your team
- Document customizations

### 2. Test Before Deploy

Both templates include GitHub Actions workflows:

```bash
# Test locally before committing
cd templates/custom-python
python main.py  # With test data

cd templates/streamlit-app
streamlit run app.py  # Test UI
```

### 3. Document Your Changes

When customizing templates:

```python
"""
Custom modifications:
- Added multi-currency support (2024-12-15)
- Integrated with external pricing API
- Added caching for better performance

Original template: templates/custom-python/main.py
"""
```

### 4. Use Version Control

Track template changes:

```bash
git add templates/
git commit -m "feat: Add custom filtering to data viewer template"
```

### 5. Share Knowledge

Create team-specific documentation:

```markdown
# Our Template Customizations

## Custom Python Template
- Always use company-specific error handler
- Include audit logging
- Follow naming convention: {project}_{date}_{version}

## Streamlit Template
- Use company color scheme (config in .streamlit/config.toml)
- Add company logo
- Include disclaimer footer
```

## Troubleshooting

### Template Doesn't Work

1. **Check dependencies**:
   ```bash
   uv pip install -r requirements.txt  # or: pip install -r requirements.txt
   ```

2. **Verify Python version**:
   ```bash
   python --version  # Should be 3.11+
   ```

3. **Test with sample data**:
   ```bash
   # Create test data structure
   mkdir -p /data/in/tables /data/out/tables
   ```

### Customization Broke Template

1. **Compare with original**:
   ```bash
   git diff templates/custom-python/main.py
   ```

2. **Check syntax**:
   ```bash
   python -m py_compile main.py
   ```

3. **Run tests**:
   ```bash
   pytest tests/
   ```

### Performance Issues

1. **Profile your code**:
   ```python
   import time
   start = time.time()
   # Your code
   print(f"Elapsed: {time.time() - start:.2f}s")
   ```

2. **Optimize data loading**:
   ```python
   # Load only required columns
   df = df[['id', 'name', 'amount']]

   # Sample large datasets
   if len(df) > 10000:
       df = df.sample(n=10000)
   ```

3. **Use caching**:
   ```python
   @st.cache_data(ttl=300)
   def expensive_operation():
       # Cached for 5 minutes
       return result
   ```

## Testing

Both templates include automated tests via GitHub Actions:

### Custom Python Template Tests

- Syntax validation
- Import checking
- Mock data processing
- Error handling validation
- Documentation completeness

### Streamlit App Template Tests

- Streamlit compatibility
- Function existence
- Configuration validation
- Security scanning
- Requirements validation

Run tests locally:

```bash
# Test Custom Python
cd templates/custom-python
python -m pytest

# Test Streamlit App
cd templates/streamlit-app
streamlit run app.py --help
```

## Contributing New Templates

Want to add a new template? Follow these guidelines:

### 1. Template Structure

```
templates/your-template/
├── README.md              # Comprehensive documentation
├── main-file.py          # Main code
├── requirements.txt      # Dependencies
├── .github/
│   └── workflows/
│       └── test-template.yml
└── examples/             # Optional: example usage
```

### 2. Documentation Requirements

Your README.md must include:

- What the template does
- When to use it
- Quick start guide
- Customization examples
- Troubleshooting section
- Best practices

### 3. Code Quality Standards

- Comprehensive docstrings
- Type hints for function parameters
- Error handling
- Logging/print statements for debugging
- Comments explaining complex logic

### 4. Testing

Include GitHub Actions workflow that tests:

- Syntax validation
- Import checking
- Basic functionality
- Documentation completeness

### 5. Example Template Checklist

- [ ] README.md with all required sections
- [ ] Working example code
- [ ] requirements.txt with pinned versions
- [ ] Inline documentation/comments
- [ ] Error handling
- [ ] GitHub Actions workflow
- [ ] Example usage in README
- [ ] Troubleshooting guide

### 6. Submit Template

```bash
# Create new template
mkdir templates/my-new-template
cd templates/my-new-template

# Add files
# ...

# Test it works
python main.py

# Commit
git add templates/my-new-template/
git commit -m "feat: Add [template name] template"

# Update main README
# Add entry to templates/README.md

# Create pull request
```

## Template Wishlist

Templates we'd love to have:

- [ ] **Keboola Writer Component**: Template for writing data to external systems
- [ ] **Keboola Extractor Component**: Template for extracting data from APIs
- [ ] **Data Quality Checker**: Automated data validation and profiling
- [ ] **ETL Pipeline Template**: Multi-step transformation pipeline
- [ ] **API Gateway**: REST API wrapper around Keboola data
- [ ] **Jupyter Notebook Integration**: Template for exploratory analysis
- [ ] **dbt Project**: Modern data transformation template
- [ ] **Airflow DAG**: Orchestration template for Keboola workflows
- [ ] **FastAPI Backend**: API service with Keboola integration
- [ ] **React Dashboard**: Frontend template with Keboola backend

Want to contribute one? See [Contributing New Templates](#contributing-new-templates) above!

## Resources

### Keboola Documentation
- [Keboola Help Center](https://help.keboola.com)
- [Developer Documentation](https://developers.keboola.com)
- [Storage API Reference](https://developers.keboola.com/integrate/storage/)
- [Custom Python Transformations](https://help.keboola.com/transformations/python/)

### Python Resources
- [Python Official Documentation](https://docs.python.org/3/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Development Tools
- [GitHub Actions](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

## Support

### Getting Help

1. **Check template documentation**: Each template has comprehensive README
2. **Review examples**: Look at example usage in README files
3. **Search issues**: Check if someone else had the same problem
4. **Ask the community**: Keboola Community Slack/Forum

### Reporting Issues

Found a bug or have a suggestion?

1. **Check existing issues**: Someone may have reported it
2. **Create detailed report**:
   - Which template?
   - What did you try?
   - What happened vs what you expected?
   - Include error messages/logs
3. **Include reproduction steps**
4. **Suggest a fix** (if you have one)

### Improvement Ideas

Have an idea to improve a template?

1. **Open an issue** describing the improvement
2. **Submit a PR** with your changes
3. **Update documentation** to reflect changes
4. **Add tests** for new functionality

## License

These templates are provided as-is for use with Keboola Platform. Feel free to:

- Use them in your projects
- Modify them for your needs
- Share them with your team
- Contribute improvements back

## Changelog

### 2024-12-15
- Initial release
- Added Custom Python template
- Added Streamlit App template
- Added comprehensive documentation
- Added automated testing workflows

---

**Happy Building!**

If these templates helped you, consider contributing improvements or new templates to help others.
