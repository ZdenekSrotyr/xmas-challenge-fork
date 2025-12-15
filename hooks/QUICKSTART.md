# Error Reporter Quick Start

Get started with the Keboola Claude Code Error Reporter in 5 minutes.

## Installation (1 minute)

```bash
# 1. Ensure GitHub CLI is installed
gh --version

# If not installed:
# macOS: brew install gh
# Linux: curl -sS https://webi.sh/gh | sh

# 2. Authenticate (if not already)
gh auth login

# 3. Verify access
gh repo view keboola/xmas-challenge

# 4. Make scripts executable (already done if you cloned)
chmod +x hooks/error-reporter.sh hooks/report-keboola-error.sh
```

Done! The error reporter is ready to use.

## First Report (30 seconds)

### Preview Mode (Dry Run)

```bash
./hooks/error-reporter.sh \
  --error-message "Your error message here" \
  --dry-run
```

You'll see exactly what would be reported without creating an issue.

### Actual Report

```bash
./hooks/error-reporter.sh \
  --error-message "Management API v2 returns 404 for valid workspace" \
  --context "Following the quickstart guide" \
  --severity high
```

Check your GitHub issues - it's there!

## Common Use Cases

### 1. API Error

```bash
./hooks/error-reporter.sh \
  --error-message "GET /v2/workspaces returns empty array" \
  --context "User has 5 workspaces visible in UI" \
  --severity high
```

### 2. Documentation Issue

```bash
./hooks/error-reporter.sh \
  --error-message "Docs say 'workspaceId' but API expects 'workspace_id'" \
  --context "Storage API endpoint /v2/storage" \
  --severity medium
```

### 3. Component Bug

```bash
./hooks/error-reporter.sh \
  --error-message "Component crashes on empty input" \
  --component "ex-generic-v2" \
  --severity low
```

## Using the Convenience Wrapper

For quick reports:

```bash
# Simple error
./hooks/report-keboola-error.sh "API timeout"

# With context
./hooks/report-keboola-error.sh "API timeout" "Listing buckets"

# With severity
./hooks/report-keboola-error.sh "API timeout" "Listing buckets" "high"
```

## Configuration

### Change Target Repository

```bash
export ERROR_REPORTER_REPO="my-org/my-repo"
```

### Disable Temporarily

```bash
export ERROR_REPORTER_DISABLED=1
```

### Enable Debug Mode

```bash
export ERROR_REPORTER_DEBUG=1
```

## Safety Features

The error reporter automatically:

- **Rate Limits**: Max 10/hour, 50/day
- **Deduplicates**: Skips identical errors within 24h
- **Sanitizes**: Only reports what you provide
- **Validates**: Checks prerequisites before reporting

## What Gets Reported?

Only what you explicitly pass:

- Error message (`--error-message`)
- Context (`--context`)
- Solution attempt (`--solution`)
- Version info (`--keboola-version`)
- Component name (`--component`)
- Severity level
- Timestamp

**No secrets, no code, no PII.**

## Best Practices

### DO

```bash
# Be specific
./hooks/error-reporter.sh \
  --error-message "Management API GET /v2/workspaces/{id} returns 404" \
  --context "Workspace exists in UI, API call fails" \
  --solution "Tried with different auth tokens, still fails" \
  --severity high
```

### DON'T

```bash
# Too vague
./hooks/error-reporter.sh \
  --error-message "API error"

# Contains secrets
./hooks/error-reporter.sh \
  --error-message "Auth failed with token abc123"
```

## Viewing Your Reports

```bash
# List all auto-reports
gh issue list --label "auto-report"

# View specific issue
gh issue view 123

# Check your report history
cat ~/.config/keboola-error-reporter/reported_errors.db
```

## Common Issues

### "GitHub CLI is not authenticated"

```bash
gh auth login
```

### "Rate limit exceeded"

Wait an hour, or use `--force`:

```bash
./hooks/error-reporter.sh \
  --error-message "Critical error" \
  --severity critical \
  --force
```

### "This error was already reported"

Either:
- Wait 24 hours (it's a duplicate)
- Use `--force` if legitimately different

```bash
./hooks/error-reporter.sh \
  --error-message "Same error, different context" \
  --force
```

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Learn integration patterns**: [INTEGRATION.md](INTEGRATION.md)
3. **Review the script**: [error-reporter.sh](error-reporter.sh)

## Help

```bash
# Show all options
./hooks/error-reporter.sh --help

# Test with debug output
export ERROR_REPORTER_DEBUG=1
./hooks/error-reporter.sh --error-message "test" --dry-run
```

## Examples

### Complete Example

```bash
./hooks/error-reporter.sh \
  --error-message "Storage API v2 bucket deletion returns 200 but bucket still exists" \
  --context "Called DELETE /v2/storage/buckets/in.c-main.test-bucket, got 200 OK, but bucket still shows in UI after 5 minutes" \
  --solution "Tried refresh, tried different buckets, same behavior" \
  --keboola-version "2.1.0" \
  --component "storage-api" \
  --severity high \
  --dry-run  # Remove this to actually create the issue
```

### Testing First

```bash
# 1. Dry run
./hooks/error-reporter.sh \
  --error-message "Test error" \
  --dry-run

# 2. Check output looks good

# 3. Remove --dry-run
./hooks/error-reporter.sh \
  --error-message "Test error"

# 4. Verify on GitHub
gh issue list --label "auto-report" | head -1
```

---

**You're ready!** Start reporting errors and help make Claude Code smarter about Keboola.

**Quick tip**: Always use `--dry-run` first when testing or when reporting sensitive information.
