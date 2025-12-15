# Integrating Error Reporter with Claude Code

This guide shows how to integrate the error reporter into Claude Code workflows.

## Quick Start

### Basic Usage

```bash
# Report a simple error
./hooks/error-reporter.sh \
  --error-message "API endpoint /v2/workspaces returns 404" \
  --dry-run

# Report with full context
./hooks/error-reporter.sh \
  --error-message "Invalid response format from Management API" \
  --context "Expected 'workspaceId' field but got 'workspace_id'" \
  --solution "Updated code to check both field names" \
  --severity high
```

## Integration Patterns

### 1. Claude Code Prompt Integration

Add this to your Claude Code system prompt or instructions:

```markdown
When you encounter Keboola-related errors:

1. First, attempt to solve the issue using available documentation
2. If the issue appears to be:
   - Outdated documentation
   - Missing API information
   - Undocumented behavior
   - Common pitfall not mentioned

3. Report it using:
   ```bash
   ./hooks/error-reporter.sh \
     --error-message "The specific error" \
     --context "What you were trying to do" \
     --solution "What you tried to fix it" \
     --severity [critical|high|medium|low]
   ```

4. Continue with workaround if available
```

### 2. Custom Slash Command

Create `.claude/commands/report-error.md`:

```markdown
# Report Error Command

When I say `/report-error`:

1. Ask me for:
   - Error message
   - Context (optional)
   - Severity (default: medium)

2. Call the error reporter:
   ```bash
   ./hooks/error-reporter.sh \
     --error-message "$ERROR_MESSAGE" \
     --context "$CONTEXT" \
     --severity $SEVERITY
   ```

3. Confirm the issue was created and provide the URL
```

### 3. Automated Detection Pattern

Example workflow for Claude Code:

```python
# In your Claude Code workflow
def try_keboola_operation():
    try:
        # Attempt Keboola API call
        result = keboola_client.workspaces.list()
    except Exception as e:
        # Check if this is a known issue
        if is_documentation_gap(e):
            # Auto-report
            subprocess.run([
                "./hooks/error-reporter.sh",
                "--error-message", str(e),
                "--context", "Listing workspaces via Management API",
                "--severity", "high"
            ])
        # Continue with error handling
        raise
```

### 4. Test Failure Reporting

Create a test wrapper that reports failures:

```bash
#!/bin/bash
# run-tests-with-reporting.sh

if ! pytest tests/; then
    # Get last test failure
    LAST_ERROR=$(pytest tests/ --tb=short 2>&1 | tail -20)

    ./hooks/error-reporter.sh \
        --error-message "Test suite failed" \
        --context "${LAST_ERROR}" \
        --component "test-suite" \
        --severity high

    exit 1
fi
```

## Integration Examples

### Example 1: API Documentation Gap

```bash
./hooks/error-reporter.sh \
  --error-message "Management API v2 documentation mentions 'workspaceId' but API returns 'workspace_id'" \
  --context "Following the official quickstart guide at https://developers.keboola.com/..." \
  --solution "Changed code to use snake_case field names" \
  --severity medium
```

### Example 2: Component Development Issue

```bash
./hooks/error-reporter.sh \
  --error-message "Component fails silently when input mapping is empty" \
  --context "Developing Python extractor following component guide" \
  --component "ex-custom-extractor" \
  --solution "Added validation: if not input_tables: raise ValueError()" \
  --severity low
```

### Example 3: Critical API Bug

```bash
./hooks/error-reporter.sh \
  --error-message "Storage API deletes wrong bucket when ID contains special characters" \
  --context "Attempting to delete bucket 'test-bucket_123'" \
  --keboola-version "2.1.0" \
  --severity critical \
  --force  # Skip dedup for critical issues
```

### Example 4: Missing Documentation

```bash
./hooks/error-reporter.sh \
  --error-message "No documentation on how to handle workspace pagination" \
  --context "Management API returns 100 workspaces max, need to fetch more" \
  --solution "Reverse-engineered from API responses: use ?offset=100&limit=100" \
  --severity medium
```

## Automated Workflows

### GitHub Actions Integration

Create `.github/workflows/report-integration-errors.yml`:

```yaml
name: Report Integration Test Errors

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Integration Tests
        id: tests
        continue-on-error: true
        run: |
          pytest tests/integration/ -v

      - name: Report Failures
        if: steps.tests.outcome == 'failure'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ./hooks/error-reporter.sh \
            --error-message "Integration tests failed" \
            --context "$(cat test-results.txt)" \
            --severity high
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Report test failures before commit

if ! pytest tests/ -q; then
    read -p "Tests failed. Report to GitHub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./hooks/error-reporter.sh \
            --error-message "Pre-commit tests failed" \
            --severity low
    fi
    exit 1
fi
```

## Best Practices

### 1. Always Use Dry-Run First

```bash
# Preview before sending
./hooks/error-reporter.sh \
  --error-message "Your error" \
  --dry-run

# Then send for real
./hooks/error-reporter.sh \
  --error-message "Your error"
```

### 2. Be Specific in Error Messages

```bash
# BAD - Too vague
--error-message "API error"

# GOOD - Specific
--error-message "Management API GET /v2/workspaces/{id} returns 404 for valid workspace ID"
```

### 3. Include Relevant Context

```bash
--context "Following step 3 of 'Getting Started with Storage API' guide (https://...)"
```

### 4. Sanitize Sensitive Data

```bash
# BAD - Contains sensitive data
--error-message "Auth failed with token abc123xyz"

# GOOD - Sanitized
--error-message "Auth failed with valid token format"
```

### 5. Use Appropriate Severity

- **critical**: Data loss, security issue, system down
- **high**: Major feature broken, incorrect behavior
- **medium**: Documentation gap, minor API issue
- **low**: Enhancement, clarification needed

## Monitoring and Metrics

### Check Reported Issues

```bash
# List auto-reported issues
gh issue list --label "auto-report" --repo keboola/xmas-challenge

# Check specific issue
gh issue view 123 --repo keboola/xmas-challenge
```

### View Your Report History

```bash
# Check deduplication cache
cat ~/.config/keboola-error-reporter/reported_errors.db

# Check rate limits
cat ~/.config/keboola-error-reporter/rate_limit.log

# Count reports today
awk -v today=$(date +%s) -v day_ago=$(($(date +%s) - 86400)) \
  '$1 > day_ago' ~/.config/keboola-error-reporter/rate_limit.log | wc -l
```

### Clear History (for testing)

```bash
# Clear all state
rm -rf ~/.config/keboola-error-reporter/

# Or just clear duplicates
rm ~/.config/keboola-error-reporter/reported_errors.db
```

## Troubleshooting Integration

### Issue: Reports not being created

1. Check if disabled:
   ```bash
   echo $ERROR_REPORTER_DISABLED
   # Should be empty or "0"
   ```

2. Check authentication:
   ```bash
   gh auth status
   ```

3. Test with debug:
   ```bash
   export ERROR_REPORTER_DEBUG=1
   ./hooks/error-reporter.sh --error-message "test"
   ```

### Issue: Too many duplicates

Increase deduplication window in `error-reporter.sh`:

```bash
DEDUP_WINDOW_HOURS=48  # Instead of 24
```

### Issue: Rate limits too restrictive

Adjust in `error-reporter.sh`:

```bash
MAX_REPORTS_PER_HOUR=20  # Instead of 10
MAX_REPORTS_PER_DAY=100  # Instead of 50
```

## Advanced Integration

### Custom Wrapper for Your Project

```bash
#!/bin/bash
# my-project-reporter.sh

# Set project-specific defaults
export ERROR_REPORTER_REPO="my-org/my-keboola-project"

# Auto-detect component from git
COMPONENT=$(basename $(git rev-parse --show-toplevel))

# Auto-detect version from package
VERSION=$(cat VERSION 2>/dev/null || echo "unknown")

# Call with project context
./hooks/error-reporter.sh \
  --error-message "$1" \
  --context "${2:-Automated report from $COMPONENT}" \
  --component "$COMPONENT" \
  --keboola-version "$VERSION" \
  --severity "${3:-medium}"
```

### Integration with Monitoring Tools

Forward alerts to GitHub:

```bash
# Webhook handler that reports to GitHub
# /webhook/keboola-error
{
  "error": "API timeout",
  "service": "keboola-storage",
  "severity": "high"
}

# Handler script
./hooks/error-reporter.sh \
  --error-message "$error" \
  --context "Alert from monitoring system" \
  --component "$service" \
  --severity "$severity"
```

## Tips for Claude Code

1. **Check Before Reporting**: Ensure it's actually a Keboola issue, not user error
2. **Provide Solutions**: Always include `--solution` if you found a workaround
3. **Use Dry-Run**: Preview sensitive reports before sending
4. **Batch Similar Issues**: Don't report the same class of error multiple times
5. **Include Links**: Reference documentation URLs in context

## Questions?

- Check the [main README](README.md)
- View [error-reporter.sh source](error-reporter.sh)
- Open an issue (or use the error reporter!)

---

**Remember**: The goal is to improve Claude Code's knowledge of Keboola. Every reported issue helps make the system smarter.
