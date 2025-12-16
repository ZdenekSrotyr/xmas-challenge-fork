# Test Report: TS-006 - Workspace ID vs Stack URL

**Test ID:** TS-006
**Test Date:** 2025-12-15
**Tester:** Claude Sonnet 4.5
**Plugin Version:** keboola-core (xmas-challenge-fork)
**Test Environment:** macOS, Claude Code

---

## Test Scenario

**Original User Request:**
> Test Scenario TS-006: Verify that Claude correctly explains the difference between Stack URL and Workspace/Project ID.

**Expected Response:**
Claude should clarify that:
- Workspace/Project ID is for UI navigation
- API uses Stack URL + token
- Example: https://connection.keboola.com/v2/storage/...
- Mentions token-based authentication

---

## Pre-Test Analysis

### Plugin Discovery

1. **Plugin Location:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/plugins/keboola-core`

2. **SKILL File:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/plugins/keboola-core/skills/keboola-knowledge/SKILL.md` (50,001 bytes)

3. **Plugin Status:** NOT INSTALLED in current Claude Code session

### Knowledge Base Review

The SKILL.md file contains:

**Workspace ID Guidance (Lines 66-99):**
- Explains THREE types of IDs:
  - Project ID: `12345` (numeric, for API calls)
  - Storage Backend ID: `KBC_USE4_361` (for SQL queries)
  - Workspace Database Name: `KEBOOLA_12345` (for transformations)

**Stack URL Handling:**
- The SKILL.md file uses `https://connection.keboola.com` as a hardcoded base URL
- Does NOT explicitly discuss "Stack URL" as a distinct concept from Project ID
- Does NOT explain regional differences or different stack domains
- All API examples use: `base_url = f"https://connection.keboola.com"`

**Authentication:**
- Clearly documented: `X-StorageApi-Token` header
- Token-based authentication explained throughout

---

## Test Execution

### Issue Identified

**CRITICAL:** The test cannot be executed as written because:

1. The keboola-core plugin is NOT currently installed in this Claude Code session
2. The test requires: `/plugin install keboola-core` to be run first
3. Without the plugin, Claude cannot access the SKILL.md knowledge base

### Discrepancy Found

There is a **mismatch** between:

**User's Test Description:**
- Focus on "Stack URL vs Workspace/Project ID"
- Expects explanation that Project ID is for UI navigation only
- Expects Stack URL is used for API calls

**Actual TEST_SCENARIOS.md (Lines 269-303):**
- TS-006 is titled "Workspace ID - Correct Identification"
- Tests distinction between Project ID, Storage Backend ID, and Workspace Database Name
- Does NOT mention "Stack URL" concept
- Focuses on three different ID types, not URL vs ID

**SKILL.md Content:**
- Addresses the three-ID confusion (Project ID, Storage Backend ID, Workspace DB Name)
- Does NOT treat "Stack URL" as a separate concept
- Hardcodes `connection.keboola.com` in all examples
- Does NOT explain regional stack URLs or multi-region deployments

---

## Analysis

### What's Missing from SKILL.md

The current knowledge base **does not adequately address:**

1. **Stack URL as a Concept:**
   - No explanation that Keboola has multiple regional stacks
   - No list of possible stack URLs (e.g., `connection.keboola.com`, `connection.eu-central-1.keboola.com`, etc.)
   - No guidance on how to find your stack URL
   - No explanation that the stack URL is independent of Project ID

2. **Stack URL vs Project ID:**
   - Doesn't clarify that Stack URL is the base domain
   - Doesn't explain that Project ID is appended to stack URL for certain operations
   - Doesn't show the relationship: `{STACK_URL}/v2/storage/...` + Token (no Project ID in URL for Storage API)

3. **Regional Considerations:**
   - No mention of multi-region deployments
   - No explanation of how region affects API endpoints

### What's Correct in SKILL.md

The knowledge base **does correctly explain:**

1. **Project ID Usage:**
   - Clearly shows Project ID in UI URLs: `connection.keboola.com/admin/projects/12345`
   - Correct usage in API calls where needed
   - Distinguishes from Storage Backend ID and Workspace DB Name

2. **Token Authentication:**
   - Excellent coverage of `X-StorageApi-Token` header
   - Multiple working code examples with token usage
   - Security best practices (using environment variables)

3. **API URL Structure:**
   - Shows correct endpoint patterns: `/v2/storage/tables/...`
   - Demonstrates proper request construction
   - Includes headers, authentication, and error handling

---

## Test Result: INCOMPLETE

### Status: ⚠️ CANNOT EXECUTE

**Reason:** Plugin not installed in current session

### Validation Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| ✅ Correctly explains workspace ID vs Stack URL | ❌ FAIL | SKILL.md doesn't discuss Stack URL as distinct concept |
| ✅ Shows correct API URL format | ✅ PASS | URLs are correctly formatted: `https://connection.keboola.com/v2/storage/...` |
| ✅ No confusion about where to use workspace ID | ⚠️ PARTIAL | Explains Project ID usage but not Stack URL relationship |
| ✅ Mentions token authentication | ✅ PASS | Excellent token authentication coverage |

**Overall Score:** 2.5 / 4 criteria met

---

## Recommendations

### 1. Update SKILL.md to Include Stack URL Guidance

Add a new section explaining:

```markdown
### Stack URL vs Project ID

**Important Distinction:**

- **Stack URL**: The base domain for your Keboola instance
  - Examples: `https://connection.keboola.com`, `https://connection.eu-central-1.keboola.com`
  - Regional/deployment-specific
  - Used as the base for ALL API calls
  - Independent of Project ID

- **Project ID**: Your workspace identifier within a stack
  - Example: `12345`
  - Used in UI URLs: `{STACK_URL}/admin/projects/{PROJECT_ID}`
  - Sometimes needed in API calls (depends on endpoint)
  - Unique within a stack

**How to Find Your Stack URL:**
1. Look at the domain when logged into Keboola UI
2. It's the `https://connection.REGION.keboola.com` part
3. Common regions:
   - US: `https://connection.keboola.com`
   - EU: `https://connection.eu-central-1.keboola.com`
   - Other regions: check your login URL

**API Usage:**
```python
# Configuration
STACK_URL = "https://connection.keboola.com"  # Your stack domain
KEBOOLA_TOKEN = os.environ["KEBOOLA_TOKEN"]   # Token is stack-specific

# Storage API - no Project ID in URL
headers = {"X-StorageApi-Token": KEBOOLA_TOKEN}
response = requests.get(
    f"{STACK_URL}/v2/storage/tables",
    headers=headers
)
```
```

### 2. Clarify Test Scenario

The test scenario needs clarification:

**Option A: Test as User Described**
- Update TS-006 to focus on Stack URL vs Project ID
- Create new test questions like: "What's my workspace ID and how do I use it with the API?"
- Expected answer should explain Stack URL + Token (not Project ID in most Storage API calls)

**Option B: Test as TEST_SCENARIOS.md Written**
- Update user's test request to match actual TS-006 content
- Focus on three ID types (Project ID, Storage Backend ID, Workspace DB Name)
- Test question: "What is my workspace ID and where do I find it?"

### 3. Install Plugin for Full Test

To complete this test properly:

```bash
# In Claude Code session
/plugin install /Users/zdeneksrotyr/Library/Mobile\ Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/plugins/keboola-core
```

Then ask:
```
What's my workspace ID and how do I use it with the API?
```

And verify Claude's response against updated criteria.

---

## Additional Findings

### Positive Aspects

1. **Comprehensive ID Type Coverage:**
   - SKILL.md thoroughly explains Project ID, Storage Backend ID, and Workspace DB Name
   - Clear table showing which ID to use in which context
   - Practical examples for each use case

2. **Strong API Examples:**
   - All code examples are syntactically correct
   - Proper error handling included
   - Authentication correctly implemented
   - Job monitoring patterns shown

3. **Good Pitfall Documentation:**
   - "Pitfall 1: Workspace ID Confusion" section addresses common errors
   - Shows wrong vs. correct usage
   - Provides troubleshooting steps

### Gaps Identified

1. **Stack URL Concept Missing:**
   - No explicit discussion of regional stacks
   - Hardcoded `connection.keboola.com` may confuse EU/other region users
   - No guidance on multi-region architectures

2. **Project ID in API URLs:**
   - Inconsistent about when Project ID appears in API calls
   - Some endpoints need it, others don't - not clearly explained
   - Storage API vs Management API differences not highlighted

3. **Real-World Deployment Context:**
   - Doesn't explain that Stack URL comes from your deployment
   - Missing connection between UI URL and API base URL
   - No troubleshooting for "wrong region" errors

---

## Conclusion

### Summary

Test TS-006 **cannot be fully executed** without installing the keboola-core plugin first. Based on knowledge base analysis, the plugin would **partially pass** the test as described:

**Would Pass:**
- API URL format (correct)
- Token authentication (excellent)

**Would Fail:**
- Stack URL as distinct concept (not covered)
- Relationship between Stack URL and Project ID (unclear)

**Needs Clarification:**
- Test scenario description doesn't match TEST_SCENARIOS.md file content
- User asked about "Stack URL vs Workspace/Project ID"
- File shows "three types of IDs" as the actual TS-006 test

### Next Steps

1. **Immediate:** Clarify which test to run (user description vs. TEST_SCENARIOS.md)
2. **Short-term:** Install plugin and execute actual test
3. **Medium-term:** Update SKILL.md with Stack URL guidance
4. **Long-term:** Add regional deployment documentation

---

## Appendix: File Locations

- **Test Scenarios:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/TEST_SCENARIOS.md`
- **Plugin Directory:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/plugins/keboola-core`
- **SKILL.md:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/plugins/keboola-core/skills/keboola-knowledge/SKILL.md`
- **This Report:** `/Users/zdeneksrotyr/Library/Mobile Documents/com~apple~CloudDocs/Sources/VsCode/component_factory/xmas-challenge-fork/TEST_REPORT_TS-006.md`

---

**Report Generated:** 2025-12-15
**Status:** INCOMPLETE - Plugin Not Installed
**Recommendation:** Install plugin and re-run test, OR clarify test scope
