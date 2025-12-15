# Test Scenarios - Keboola AI-Kit

## Overview

This document contains comprehensive test scenarios based on the success criteria from the challenge. Each scenario includes setup, execution steps, expected results, and validation criteria.

---

## Success Criteria Mapping

| # | Success Criterion | Test Scenarios | Status |
|---|-------------------|----------------|--------|
| 1 | Claude writes working Python code for any Keboola API endpoint | TS-001 to TS-005 | ⏳ |
| 2 | Zero "workspace ID confusion" issues | TS-006 to TS-008 | ⏳ |
| 3 | Claude can read/write Input/Output mapping | TS-009 to TS-011 | ⏳ |
| 4 | End-user describes in business language, Claude does it | TS-012 to TS-014 | ⏳ |
| 5 | 80%+ issues correctly auto-triaged | TS-015 to TS-017 | ⏳ |
| 6 | Knowledge base continuously improves | TS-018 to TS-020 | ⏳ |

---

## Test Scenario 1: Storage API - Read Table

**ID:** TS-001
**Success Criterion:** #1 - Claude writes working Python code for any Keboola API endpoint
**Priority:** HIGH
**Type:** Functional

### Setup
- Plugin keboola-core installed
- Test Keboola workspace available

### Test Steps

**Step 1:** Ask Claude
```
I need to read a table from Keboola Storage.
The table is "in.c-main.customers" and I want to save it to a local file.
```

**Step 2:** Claude should provide code using Storage API

**Step 3:** Verify code includes:
- Correct API endpoint (Storage API)
- Proper authentication (token handling)
- Table export functionality
- Job status monitoring
- Error handling

### Expected Result

```python
import requests
import time
import os

# Configuration
KEBOOLA_STACK_URL = "https://connection.keboola.com"
KEBOOLA_TOKEN = os.environ["KEBOOLA_TOKEN"]
TABLE_ID = "in.c-main.customers"

# Export table
headers = {"X-StorageApi-Token": KEBOOLA_TOKEN}
response = requests.post(
    f"{KEBOOLA_STACK_URL}/v2/storage/tables/{TABLE_ID}/export-async",
    headers=headers
)
response.raise_for_status()
job_id = response.json()["id"]

# Wait for job
while True:
    job_response = requests.get(
        f"{KEBOOLA_STACK_URL}/v2/storage/jobs/{job_id}",
        headers=headers
    )
    job = job_response.json()

    if job["status"] == "success":
        file_url = job["results"]["file"]["url"]
        break
    elif job["status"] in ["error", "cancelled"]:
        raise Exception(f"Job failed: {job.get('error', {}).get('message')}")

    time.sleep(2)

# Download file
file_response = requests.get(file_url)
with open("customers.csv", "wb") as f:
    f.write(file_response.content)
```

### Validation Criteria
- ✅ Code is syntactically correct
- ✅ Uses correct API endpoints
- ✅ Includes authentication
- ✅ Monitors job status (doesn't just fire and forget)
- ✅ Has error handling
- ✅ Code is runnable with minimal changes (just add token)

---

## Test Scenario 2: Storage API - Write Table

**ID:** TS-002
**Success Criterion:** #1 - Claude writes working Python code for any Keboola API endpoint
**Priority:** HIGH
**Type:** Functional

### Setup
- Plugin keboola-core installed
- CSV file to upload available

### Test Steps

**Step 1:** Ask Claude
```
I have a CSV file "output.csv" and I want to upload it to Keboola Storage
as a new table "out.c-results.processed_data" with incremental loading.
```

**Step 2:** Verify code includes:
- File upload to Storage
- Table creation with proper parameters
- Incremental load settings
- Primary key handling

### Expected Result

Code should:
- Upload CSV to Storage Files
- Create/import table with `incremental: true`
- Handle primary keys correctly
- Monitor import job status

### Validation Criteria
- ✅ Handles file upload correctly
- ✅ Sets incremental load parameter
- ✅ Mentions primary key requirement
- ✅ Monitors import job
- ✅ Error handling included

---

## Test Scenario 3: Jobs API - Run Transformation

**ID:** TS-003
**Success Criterion:** #1 - Claude writes working Python code for any Keboola API endpoint
**Priority:** HIGH
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
How do I run a specific Keboola transformation using Python?
My transformation config ID is "12345678".
```

**Step 2:** Verify code uses Jobs API (not Queue API)

### Expected Result

```python
import requests
import os
import time

KEBOOLA_STACK_URL = "https://connection.keboola.com"
KEBOOLA_TOKEN = os.environ["KEBOOLA_TOKEN"]
CONFIG_ID = "12345678"

headers = {"X-StorageApi-Token": KEBOOLA_TOKEN}

# Run transformation
response = requests.post(
    f"{KEBOOLA_STACK_URL}/v2/storage/jobs",
    headers=headers,
    json={
        "component": "keboola.snowflake-transformation",
        "mode": "run",
        "configData": {"id": CONFIG_ID}
    }
)
response.raise_for_status()
job_id = response.json()["id"]

# Monitor job...
```

### Validation Criteria
- ✅ Uses Jobs API endpoint
- ✅ Correct component ID format
- ✅ Monitors job completion
- ✅ Handles errors
- ✅ Gets job logs if needed

---

## Test Scenario 4: Custom Python Deployment

**ID:** TS-004
**Success Criterion:** #1 - Claude writes working Python code for any Keboola API endpoint
**Priority:** HIGH
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
I want to create a Custom Python transformation that reads data from
one table, processes it, and writes to another table. How do I structure this?
```

**Step 2:** Claude should provide complete component structure

### Expected Result

Claude should provide:
- Complete directory structure
- Code using `keboola.component`
- Proper Input/Output mapping configuration
- Manifest file handling
- Dockerfile

### Validation Criteria
- ✅ Uses keboola.component library
- ✅ Shows Input/Output mapping config
- ✅ Explains manifest files
- ✅ Includes Dockerfile
- ✅ Shows local testing approach

---

## Test Scenario 5: MCP Server vs Direct API

**ID:** TS-005
**Success Criterion:** #1 - Claude writes working Python code
**Priority:** MEDIUM
**Type:** Decision-Making

### Test Steps

**Step 1:** Ask Claude
```
Should I use the Keboola MCP server or write direct API calls
for my data processing pipeline?
```

**Step 2:** Verify Claude provides decision framework

### Expected Result

Claude should explain:
- **Use MCP for:** validation, schemas, small queries, prototyping
- **Use Storage API for:** large datasets, production pipelines, batch processing
- **Use Components for:** complex logic, external systems, scheduled operations

With code examples for each approach.

### Validation Criteria
- ✅ Provides clear decision framework
- ✅ Shows examples of each approach
- ✅ Explains trade-offs
- ✅ Mentions when to combine approaches

---

## Test Scenario 6: Workspace ID - Correct Identification

**ID:** TS-006
**Success Criterion:** #2 - Zero "workspace ID confusion"
**Priority:** CRITICAL
**Type:** Knowledge

### Test Steps

**Step 1:** Ask Claude
```
What is my workspace ID and where do I find it?
```

**Step 2:** Verify Claude distinguishes between:
- Project ID (for API calls)
- Storage Backend ID (for SQL queries)
- Workspace Database Name (for transformations)

### Expected Result

Claude should provide comparison table:

| Type | Example | Use For |
|------|---------|---------|
| Project ID | 12345 | API calls, UI URL |
| Storage Backend ID | KBC_USE4_361 | Direct SQL queries |
| Workspace Database Name | KEBOOLA_12345 | Transformation SQL |

### Validation Criteria
- ✅ Distinguishes between all three types
- ✅ Provides clear examples
- ✅ Explains when to use each
- ✅ Shows where to find each in UI

---

## Test Scenario 7: Workspace ID - API Context

**ID:** TS-007
**Success Criterion:** #2 - Zero "workspace ID confusion"
**Priority:** CRITICAL
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
I'm writing a Python script to call the Keboola API.
What workspace ID should I use?
```

**Step 2:** Verify Claude recommends Project ID

### Expected Result

Claude should:
- Recommend using **Project ID** (numeric, e.g., 12345)
- Explain it's in the URL: `connection.keboola.com/admin/projects/12345`
- Show example API call with Project ID in URL path
- **NOT** recommend Storage Backend ID or DB Name

### Validation Criteria
- ✅ Recommends correct ID type (Project ID)
- ✅ Shows how to find it
- ✅ Provides example URL
- ✅ Doesn't confuse with other ID types

---

## Test Scenario 8: Workspace ID - SQL Context

**ID:** TS-008
**Success Criterion:** #2 - Zero "workspace ID confusion"
**Priority:** CRITICAL
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
I'm writing a SQL query in Snowflake to access Keboola tables directly.
What should I use as the database/schema identifier?
```

**Step 2:** Verify Claude recommends correct identifier for SQL context

### Expected Result

Claude should:
- For **direct SQL queries**: Use Storage Backend ID (e.g., `KBC_USE4_361`)
- For **transformations**: Use Workspace Database Name (e.g., `KEBOOLA_12345`)
- Show example: `SELECT * FROM "KBC_USE4_361"."in.c-main"."customers"`

### Validation Criteria
- ✅ Distinguishes between direct SQL and transformations
- ✅ Uses correct identifier for each context
- ✅ Shows fully qualified table names
- ✅ Explains quoting rules

---

## Test Scenario 9: Input Mapping - Read Files

**ID:** TS-009
**Success Criterion:** #3 - Claude can read/write Input/Output mapping
**Priority:** HIGH
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
I have a Custom Python component with input mapping configured.
How do I read the input tables in my code?
```

**Step 2:** Verify Claude explains data directory structure

### Expected Result

Claude should explain:
- Input tables are in `/data/in/tables/`
- Filenames from manifest: `/data/in/tables/{table_name}.csv`
- How to read manifest: `/data/in/tables/{table_name}.csv.manifest`
- Example code reading CSV with pandas

```python
import pandas as pd
import json

# Read input table
df = pd.read_csv("/data/in/tables/customers.csv")

# Read manifest (optional - for metadata)
with open("/data/in/tables/customers.csv.manifest") as f:
    manifest = json.load(f)
    print(f"Table ID: {manifest['id']}")
```

### Validation Criteria
- ✅ Shows correct path `/data/in/tables/`
- ✅ Explains manifest files
- ✅ Provides working code example
- ✅ Mentions CSV format

---

## Test Scenario 10: Output Mapping - Write Files

**ID:** TS-010
**Success Criterion:** #3 - Claude can read/write Input/Output mapping
**Priority:** HIGH
**Type:** Functional

### Test Steps

**Step 1:** Ask Claude
```
How do I write output tables in my Custom Python component
so they get loaded back to Keboola Storage?
```

**Step 2:** Verify Claude explains output directory and manifests

### Expected Result

Claude should explain:
- Write to `/data/out/tables/`
- Create manifest file for each table
- Manifest should specify: destination, incremental, primary_key

```python
import pandas as pd
import json

# Write output CSV
df.to_csv("/data/out/tables/results.csv", index=False)

# Create manifest
manifest = {
    "destination": "out.c-results.processed",
    "incremental": True,
    "primary_key": ["id"],
    "delimiter": ",",
    "enclosure": '"'
}
with open("/data/out/tables/results.csv.manifest", "w") as f:
    json.dump(manifest, f, indent=2)
```

### Validation Criteria
- ✅ Shows correct output path
- ✅ Explains manifest requirement
- ✅ Shows manifest structure
- ✅ Includes incremental and primary_key
- ✅ Provides working code

---

## Test Scenario 11: Input/Output Mapping - Configuration

**ID:** TS-011
**Success Criterion:** #3 - Claude can read/write Input/Output mapping
**Priority:** MEDIUM
**Type:** Configuration

### Test Steps

**Step 1:** Ask Claude
```
How do I configure input and output mapping for my component in the Keboola UI?
```

**Step 2:** Verify Claude explains both UI and JSON config

### Expected Result

Claude should show:
- UI approach: Data In/Out tabs in component configuration
- JSON config structure:
```json
{
  "storage": {
    "input": {
      "tables": [
        {
          "source": "in.c-main.customers",
          "destination": "customers.csv"
        }
      ]
    },
    "output": {
      "tables": [
        {
          "source": "results.csv",
          "destination": "out.c-results.processed"
        }
      ]
    }
  }
}
```

### Validation Criteria
- ✅ Explains UI configuration
- ✅ Shows JSON structure
- ✅ Maps Storage table ID ↔ local file
- ✅ Shows both input and output

---

## Test Scenario 12: Business Language - Data Export

**ID:** TS-012
**Success Criterion:** #4 - End-user describes in business language
**Priority:** HIGH
**Type:** User Experience

### Test Steps

**Step 1:** Ask Claude (as non-technical user)
```
I need to get my customer data out of Keboola so I can analyze it in Excel.
```

**Step 2:** Claude should translate to technical solution

### Expected Result

Claude should:
1. Understand "get data out" = export from Storage
2. Provide simple solution (not requiring coding if possible)
3. Offer multiple approaches:
   - UI: Export button in Tables section
   - API: Python script to download
   - Data App: Streamlit app template

### Validation Criteria
- ✅ Understands business intent
- ✅ Provides non-technical solution first
- ✅ Offers technical alternatives
- ✅ Explains in simple terms

---

## Test Scenario 13: Business Language - Data Processing

**ID:** TS-013
**Success Criterion:** #4 - End-user describes in business language
**Priority:** HIGH
**Type:** User Experience

### Test Steps

**Step 1:** Ask Claude (as business user)
```
I want to calculate the total revenue per customer and save it back to Keboola.
```

**Step 2:** Claude should understand and provide solution

### Expected Result

Claude should:
1. Recognize this as: read → transform → write
2. Suggest appropriate method:
   - SQL transformation (if data already in Keboola)
   - Custom Python (if complex logic needed)
3. Provide working example with business context

```sql
-- SQL Transformation
CREATE TABLE "out.c-results.customer_revenue" AS
SELECT
    customer_id,
    SUM(order_amount) as total_revenue
FROM "in.c-main.orders"
GROUP BY customer_id;
```

### Validation Criteria
- ✅ Translates business logic correctly
- ✅ Chooses appropriate tool
- ✅ Provides working solution
- ✅ Explains what the code does in business terms

---

## Test Scenario 14: Business Language Mapping Table

**ID:** TS-014
**Success Criterion:** #4 - End-user describes in business language
**Priority:** MEDIUM
**Type:** Knowledge

### Test Steps

**Step 1:** Ask Claude
```
I'm not technical - can you translate common business tasks to Keboola operations?
```

### Expected Result

Claude should provide mapping table:

| Business Language | Keboola Operation | Tool |
|-------------------|-------------------|------|
| "Get data out" | Export table | Storage API / UI |
| "Load data in" | Import table | Storage API / Extractor |
| "Calculate totals" | Transformation | SQL / Python |
| "Schedule daily" | Flow / Orchestration | Flows |
| "Send report" | Writer / Data App | Writer component |

### Validation Criteria
- ✅ Provides comprehensive mapping
- ✅ Includes common business terms
- ✅ Shows appropriate tools
- ✅ Links to examples

---

## Test Scenario 15: Auto-Triage - API Error

**ID:** TS-015
**Success Criterion:** #5 - 80%+ issues correctly auto-triaged
**Priority:** HIGH
**Type:** Automation

### Test Steps

**Step 1:** Create GitHub Issue with label "auto-report"
```yaml
Title: "Storage API returns 404 for valid table ID"

Body:
Error: GET /v2/storage/tables/in.c-main.customers returned 404

Context: Following the quickstart guide to read a table

Attempted:
- Verified table exists in UI
- Token has correct permissions
- Table ID copied from Storage browser

Keboola Version: Stack USE region
```

**Step 2:** Wait for auto-triage workflow (~30 seconds)

**Step 3:** Check issue for triage comment

### Expected Result

Triage comment should include:
- **Category:** api-error
- **Confidence:** 85-95%
- **Analysis:** Likely table ID format issue or permissions
- **Suggested Fix:** Check fully qualified table name
- **Auto-trigger:** propose-fix workflow if confidence ≥ 80%

### Validation Criteria
- ✅ Workflow triggers automatically
- ✅ Categorizes correctly as "api-error"
- ✅ Confidence score reasonable (80-100%)
- ✅ Analysis is accurate
- ✅ Suggests appropriate fix

---

## Test Scenario 16: Auto-Triage - Outdated Documentation

**ID:** TS-016
**Success Criterion:** #5 - 80%+ issues correctly auto-triaged
**Priority:** HIGH
**Type:** Automation

### Test Steps

**Step 1:** Create GitHub Issue with label "auto-report"
```yaml
Title: "Documentation shows old API endpoint"

Body:
Error: The SKILL.md shows endpoint /v1/storage/tables but the API now uses /v2/storage/tables

Context: Following Storage API examples in keboola-core plugin

Attempted:
- Tried v1 endpoint (404 error)
- Checked official docs (shows v2)
- Code example needs update
```

**Step 2:** Wait for auto-triage

### Expected Result

Triage should:
- **Category:** outdated-docs
- **Confidence:** 90-100%
- **Analysis:** Documentation needs update to v2
- **Suggested Fix:** Update SKILL.md Storage API section
- **PR Generated:** If confidence ≥ 80%

### Validation Criteria
- ✅ Correctly categorized as "outdated-docs"
- ✅ High confidence (90%+)
- ✅ Identifies specific file to update
- ✅ Generates PR with fix

---

## Test Scenario 17: Auto-Triage - Common Pitfall

**ID:** TS-017
**Success Criterion:** #5 - 80%+ issues correctly auto-triaged
**Priority:** HIGH
**Type:** Automation

### Test Steps

**Step 1:** Create GitHub Issue
```yaml
Title: "Confused about which workspace ID to use"

Body:
Error: I see multiple IDs in Keboola - which one should I use for API calls?

Context: Writing Python script to call Storage API

Attempted:
- Tried Storage Backend ID (failed)
- Not sure which ID is correct
```

**Step 2:** Wait for auto-triage

### Expected Result

Triage should:
- **Category:** pitfall
- **Confidence:** 95-100%
- **Analysis:** Common workspace ID confusion
- **Resolution:** Already documented in SKILL.md
- **Action:** Add link to existing documentation section

### Validation Criteria
- ✅ Recognizes as known pitfall
- ✅ Very high confidence
- ✅ Links to existing solution
- ✅ May suggest improving discoverability

---

## Test Scenario 18: Knowledge Base Update - Merged PR

**ID:** TS-018
**Success Criterion:** #6 - Knowledge base continuously improves
**Priority:** HIGH
**Type:** Integration

### Test Steps

**Step 1:** Let auto-triage generate PR (from TS-016)

**Step 2:** Review and merge PR

**Step 3:** Verify SKILL.md updated

**Step 4:** Create new issue with same problem

**Step 5:** Verify Claude now has correct information

### Expected Result

After PR merged:
- SKILL.md contains updated information
- Claude's responses use new information
- Same issue won't occur again

### Validation Criteria
- ✅ PR updates correct file
- ✅ Changes are accurate
- ✅ Claude uses updated knowledge
- ✅ Issue doesn't recur

---

## Test Scenario 19: Knowledge Base - Metrics Tracking

**ID:** TS-019
**Success Criterion:** #6 - Knowledge base continuously improves
**Priority:** MEDIUM
**Type:** Monitoring

### Test Steps

**Step 1:** Run metrics for 30 days of simulated data
```bash
cd scripts/metrics
./example-workflow.sh
```

**Step 2:** Check dashboard output

### Expected Result

Dashboard should show:
- **Triage Accuracy:** Trending upward over time
- **Error Reduction:** Duplicate issues decreasing
- **PR Merge Rate:** Improving (more accepted fixes)
- **Time Saved:** Increasing month over month

### Validation Criteria
- ✅ All metrics calculated correctly
- ✅ Trends shown visually
- ✅ Targets indicated (80%, 70%, etc.)
- ✅ Export to HTML/JSON works

---

## Test Scenario 20: Knowledge Base - Validation Loop

**ID:** TS-020
**Success Criterion:** #6 - Knowledge base continuously improves
**Priority:** HIGH
**Type:** Automation

### Test Steps

**Step 1:** Trigger daily validation workflow
```bash
# GitHub Actions: validate-examples.yml
```

**Step 2:** Introduce broken link in SKILL.md

**Step 3:** Wait for next validation run

### Expected Result

Validation should:
- Detect broken link
- Create auto-report issue
- Fail the workflow
- Notify maintainers

### Validation Criteria
- ✅ Detects broken links
- ✅ Validates Python syntax
- ✅ Creates issue for failures
- ✅ Runs on schedule (daily)

---

## Error Reporting Behavior Tests

### Test Scenario 21: Agent Error - Should Report?

**ID:** TS-021
**Priority:** CRITICAL
**Type:** Behavior Analysis

**Scenario A: User Says "You Did It Wrong"**

**Test Steps:**
1. Ask Claude to generate code
2. Tell Claude: "This is wrong, it doesn't work"
3. Observe behavior

**Expected Behavior:**
- Claude should **ASK** if this should be reported
- Claude should **NOT** automatically report without confirmation
- Claude should try to fix the issue first
- Only report if:
  - User explicitly says "report this"
  - Problem is with the knowledge base (not user's environment)
  - Claude cannot resolve after attempts

**Validation:**
- ✅ Asks before reporting
- ✅ Attempts to fix first
- ✅ Doesn't spam issues with user errors

---

**Scenario B: Knowledge Base Gap Detected**

**Test Steps:**
1. Ask about something not covered in SKILL.md
2. Claude admits it doesn't know
3. Observe behavior

**Expected Behavior:**
- Claude should recognize knowledge gap
- Claude should suggest reporting it
- Should ask: "Should I create an issue to add this to the knowledge base?"
- Only report if user confirms

---

**Scenario C: Outdated Information Detected**

**Test Steps:**
1. User provides evidence that SKILL.md info is wrong
2. User shows official docs with different info
3. Observe behavior

**Expected Behavior:**
- Claude should recognize documentation is outdated
- Claude should **proactively suggest** reporting
- Should create issue with:
  - Current (wrong) information
  - Correct information
  - Source of truth
  - Confidence: HIGH

---

## Test Execution Plan

### Phase 1: Core Functionality (TS-001 to TS-014)
**Timeline:** Day 1-2
**Goal:** Verify basic knowledge works

1. Install plugin in fresh Claude Code instance
2. Run through all API tests (TS-001 to TS-005)
3. Verify workspace ID guidance (TS-006 to TS-008)
4. Test Input/Output mapping (TS-009 to TS-011)
5. Test business language translation (TS-012 to TS-014)

### Phase 2: Self-Healing System (TS-015 to TS-020)
**Timeline:** Day 3-4
**Goal:** Verify automation works

1. Setup GitHub repository with Actions enabled
2. Add ANTHROPIC_API_KEY secret
3. Test auto-triage (TS-015 to TS-017)
4. Test knowledge updates (TS-018)
5. Test metrics (TS-019)
6. Test validation (TS-020)

### Phase 3: Error Reporting Behavior (TS-021)
**Timeline:** Day 5
**Goal:** Verify intelligent error reporting

1. Test user correction scenarios
2. Test knowledge gap scenarios
3. Test outdated info scenarios
4. Verify no spam issues created

---

## Success Metrics

### Target Accuracy Rates

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code Generation Accuracy | 95%+ | TS-001 to TS-005 pass rate |
| Workspace ID Correct Usage | 100% | TS-006 to TS-008 pass rate |
| I/O Mapping Correct | 100% | TS-009 to TS-011 pass rate |
| Business Translation | 90%+ | TS-012 to TS-014 user satisfaction |
| Triage Accuracy | 80%+ | TS-015 to TS-017 correct categorization |
| KB Improvement | Measurable | TS-018 to TS-020 trend positive |

---

## Test Results Template

```markdown
## Test Run: [Date]

### Environment
- Plugin Version:
- Claude Code Version:
- Tester:

### Results Summary
- Tests Passed: X / 21
- Tests Failed: Y
- Tests Skipped: Z

### Detailed Results

#### TS-001: Storage API Read
- Status: ✅ PASS / ❌ FAIL / ⏭️ SKIP
- Notes:
- Issues Found:

[Continue for all tests...]

### Issues Discovered
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

## Appendix: Test Data

### Sample Keboola Configuration

```json
{
  "test_workspace": {
    "project_id": "12345",
    "storage_backend_id": "KBC_USE4_361",
    "db_name": "KEBOOLA_12345",
    "token": "[TEST_TOKEN]",
    "stack_url": "https://connection.keboola.com"
  },
  "test_tables": {
    "input": "in.c-main.customers",
    "output": "out.c-test.results"
  }
}
```

### Sample Test Files

- `test_data/customers.csv` - Sample input data
- `test_data/expected_output.csv` - Expected results
- `test_data/config.json` - Component configuration

---

## Notes

- All test scenarios assume keboola-core plugin is installed
- Some tests require real Keboola workspace (development/testing account)
- Simulated data can be used for metrics tests (TS-019)
- Error reporting tests (TS-021) should be done manually to verify behavior

---

**Last Updated:** December 15, 2025
**Version:** 1.0
**Status:** Ready for Execution
