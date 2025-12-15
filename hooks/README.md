# Keboola Claude Code Error Reporter

Automatically reports Keboola-related errors encountered by Claude Code to GitHub Issues, enabling a self-healing knowledge system.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Examples](#examples)
- [Privacy & Data Considerations](#privacy--data-considerations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Overview

The Error Reporter is a Bash script that integrates with Claude Code to automatically report errors, outdated documentation, and missing features to GitHub Issues. This creates a feedback loop where:

1. Claude encounters a Keboola-related problem
2. Error is automatically reported with context
3. AI/Human triages and fixes the issue
4. Knowledge base is updated
5. Claude knows how to handle it next time

### Key Features

- **Automatic Issue Creation**: Creates structured GitHub Issues with all relevant context
- **Rate Limiting**: Prevents spam with configurable hourly/daily limits
- **Deduplication**: Avoids creating duplicate issues for the same error
- **Privacy-Aware**: Only reports what you explicitly pass to it
- **Dry-Run Mode**: Preview what would be reported before sending
- **Severity Levels**: Categorize issues by impact (critical/high/medium/low)

## Installation

### Prerequisites

1. **GitHub CLI (`gh`)**: Required for creating issues

   ```bash
   # macOS
   brew install gh

   # Linux
   curl -sS https://webi.sh/gh | sh

   # Or download from https://cli.github.com/
   ```

2. **Authenticate GitHub CLI**:

   ```bash
   gh auth login
   ```

3. **Verify Access** to the target repository:

   ```bash
   gh repo view keboola/xmas-challenge
   ```

### Basic Setup

1. **Make the script executable** (if not already):

   ```bash
   chmod +x hooks/error-reporter.sh
   ```

2. **Test the installation**:

   ```bash
   ./hooks/error-reporter.sh --help
   ```

3. **Run a dry-run** to verify configuration:

   ```bash
   ./hooks/error-reporter.sh \
     --error-message "Test error" \
     --dry-run
   ```

### Integration with Claude Code

#### Option 1: Manual Invocation

Call the script directly when Claude encounters an error:

```bash
./hooks/error-reporter.sh \
  --error-message "WorkspaceId not found in response" \
  --context "Trying to list workspaces using Management API" \
  --solution "Added error handling for missing fields" \
  --keboola-version "1.2.3" \
  --severity high
```

#### Option 2: Claude Prompt Integration

Add to your Claude Code prompts/instructions:

```
When you encounter a Keboola-related error that seems like a knowledge gap:
1. Document the error, context, and attempted solution
2. Call the error reporter: ./hooks/error-reporter.sh --error-message "..." --context "..." --solution "..."
```

#### Option 3: Wrapper Script

Create a convenience wrapper for common scenarios:

```bash
#!/bin/bash
# report-keboola-error.sh

./hooks/error-reporter.sh \
  --error-message "$1" \
  --context "${2:-}" \
  --severity "${3:-medium}"
```

## Usage

### Command Line Options

```bash
./hooks/error-reporter.sh [OPTIONS]

Options:
  --error-message TEXT     The error message (required)
  --context TEXT          Additional context about what was attempted
  --solution TEXT         What Claude tried to fix it
  --keboola-version TEXT  Keboola version if known
  --component TEXT        Component name if applicable
  --severity LEVEL        critical|high|medium|low (default: medium)
  --dry-run              Don't create issue, just show what would be created
  --force                Skip deduplication check
  --help                 Show this help message
```

### Environment Variables

Configure the behavior via environment variables:

```bash
# Change target repository
export ERROR_REPORTER_REPO="your-org/your-repo"

# Disable error reporting
export ERROR_REPORTER_DISABLED=1

# Enable debug output
export ERROR_REPORTER_DEBUG=1
```

### Severity Levels

Choose the appropriate severity:

- **`critical`**: System-breaking errors, security issues
- **`high`**: Major functionality broken, incorrect API behavior
- **`medium`**: Documentation gaps, minor API issues (default)
- **`low`**: Improvements, clarifications, nice-to-haves

## How It Works

### 1. Validation Phase

- Checks if GitHub CLI is installed and authenticated
- Verifies access to target repository
- Validates input parameters

### 2. Safety Checks

#### Rate Limiting

- **Hourly Limit**: Maximum 10 reports per hour
- **Daily Limit**: Maximum 50 reports per day
- Prevents accidental spam from automation loops
- Override with `--force` if needed

#### Deduplication

- Computes hash of error message + component
- Checks if same error was reported in last 24 hours
- Prevents duplicate issues for the same problem
- Override with `--force` for legitimate duplicates

### 3. Issue Creation

Creates a structured GitHub Issue with:

- **Title**: `[Auto-Report] Component: Error message...`
- **Labels**:
  - `auto-report` - Identifies auto-generated issues
  - `needs-triage` - Signals human review needed
  - `priority:*` - Severity-based priority
  - `component:*` - Component tag if provided
- **Body**: Formatted markdown with all context

### 4. State Management

- Records reported errors in `~/.config/keboola-error-reporter/`
- Tracks rate limits and deduplication data
- Automatically cleans up old entries

### File Structure

```
~/.config/keboola-error-reporter/
├── reported_errors.db    # Deduplication cache
└── rate_limit.log        # Rate limiting log
```

## Configuration

### Customizing Rate Limits

Edit the script constants:

```bash
MAX_REPORTS_PER_HOUR=10    # Change to your needs
MAX_REPORTS_PER_DAY=50     # Adjust based on usage
DEDUP_WINDOW_HOURS=24      # Deduplication time window
```

### Changing Target Repository

```bash
# Temporary
export ERROR_REPORTER_REPO="my-org/my-repo"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ERROR_REPORTER_REPO="my-org/my-repo"' >> ~/.bashrc
```

### Disabling Error Reporting

```bash
# Temporarily disable
export ERROR_REPORTER_DISABLED=1

# Or for specific commands
ERROR_REPORTER_DISABLED=1 ./hooks/error-reporter.sh ...
```

## Examples

### Example 1: API Error

```bash
./hooks/error-reporter.sh \
  --error-message "404 Not Found: /v2/workspaces/12345/components" \
  --context "Attempting to list components in workspace 12345" \
  --solution "Verified workspace ID exists, but endpoint returns 404" \
  --keboola-version "2.0.1" \
  --severity high
```

**Creates issue:** `[Auto-Report] 404 Not Found: /v2/workspaces/12345/components`

### Example 2: Documentation Gap

```bash
./hooks/error-reporter.sh \
  --error-message "Documentation says use 'workspaceId' but API expects 'workspace_id'" \
  --context "Following quickstart guide for Storage API" \
  --solution "Changed to snake_case, now works" \
  --severity medium
```

**Creates issue:** `[Auto-Report] Documentation says use 'workspaceId' but API expects...`

### Example 3: Component-Specific Issue

```bash
./hooks/error-reporter.sh \
  --error-message "Component fails on empty input mapping" \
  --context "Python extractor with no input tables configured" \
  --component "ex-generic-v2" \
  --solution "Added validation for empty input" \
  --severity low
```

**Creates issue:** `[Auto-Report] ex-generic-v2: Component fails on empty input mapping`

### Example 4: Dry Run (Preview)

```bash
./hooks/error-reporter.sh \
  --error-message "Rate limit exceeded" \
  --severity critical \
  --dry-run
```

**Output:**
```
[ERROR-REPORTER] DRY RUN - Would create issue with:

Repository: keboola/xmas-challenge
Title: [Auto-Report] Rate limit exceeded
Labels: auto-report,needs-triage,priority:critical

Body:
----------------------------------------
## Error Report
...
----------------------------------------
```

### Example 5: Force Report (Skip Checks)

```bash
./hooks/error-reporter.sh \
  --error-message "Same error but different context" \
  --force
```

Bypasses deduplication and rate limiting checks.

## Privacy & Data Considerations

### What Gets Reported

The error reporter **only** sends information you explicitly provide:

- Error message (`--error-message`)
- Context (`--context`)
- Attempted solution (`--solution`)
- Keboola version (`--keboola-version`)
- Component name (`--component`)
- Severity level
- Timestamp

### What Does NOT Get Reported

- Your code or file contents
- API keys or credentials
- Personal identifiable information (PII)
- Workspace IDs or configuration IDs (unless in error message)
- System information beyond what's shown

### Security Best Practices

1. **Review Before Reporting**: Use `--dry-run` to preview
2. **Sanitize Error Messages**: Remove sensitive data before reporting
3. **Check Context**: Ensure no secrets in `--context` or `--solution`
4. **Workspace IDs**: Consider if they should be shared publicly

### Example: Sanitizing Sensitive Data

```bash
# BAD - Contains API token
./hooks/error-reporter.sh \
  --error-message "API error: Invalid token abc123xyz"

# GOOD - Sanitized
./hooks/error-reporter.sh \
  --error-message "API error: Invalid token [REDACTED]"
```

### Opt-Out

If you prefer not to use automated reporting:

```bash
# Disable globally
export ERROR_REPORTER_DISABLED=1
```

## Troubleshooting

### Issue: "GitHub CLI is not installed"

**Solution:** Install GitHub CLI:
```bash
brew install gh  # macOS
# or visit https://cli.github.com/
```

### Issue: "GitHub CLI is not authenticated"

**Solution:** Authenticate:
```bash
gh auth login
```

### Issue: "Cannot access repository"

**Causes:**
- Repository doesn't exist
- You don't have write access
- Wrong repository name

**Solution:**
```bash
# Test access
gh repo view keboola/xmas-challenge

# Change repository
export ERROR_REPORTER_REPO="your-org/your-repo"
```

### Issue: "Rate limit exceeded"

**Cause:** Too many reports in short time

**Solutions:**
```bash
# Wait for limit to reset (1 hour or 1 day)

# Or force the report (use sparingly)
./hooks/error-reporter.sh --error-message "..." --force

# Or adjust limits in the script
```

### Issue: "This error was already reported"

**Cause:** Duplicate detection within 24 hours

**Solutions:**
```bash
# Wait for deduplication window (24h)

# Or force if legitimately different
./hooks/error-reporter.sh --error-message "..." --force
```

### Issue: Script runs but no issue created

**Debug Steps:**
```bash
# Enable debug mode
export ERROR_REPORTER_DEBUG=1
./hooks/error-reporter.sh --error-message "test"

# Check gh CLI can create issues
gh issue create --repo keboola/xmas-challenge --title "Test" --body "Test"

# Verify script is executable
ls -l hooks/error-reporter.sh
# Should show: -rwxr-xr-x
```

## Development

### Testing

```bash
# Test with dry-run
./hooks/error-reporter.sh \
  --error-message "Test error" \
  --context "Test context" \
  --dry-run

# Test against a sandbox repo
export ERROR_REPORTER_REPO="your-username/test-repo"
./hooks/error-reporter.sh --error-message "Test"

# Test rate limiting
for i in {1..12}; do
  ./hooks/error-reporter.sh --error-message "Test $i"
done
# Should fail after 10
```

### Debugging

```bash
# Enable debug output
export ERROR_REPORTER_DEBUG=1

# Check state files
ls -la ~/.config/keboola-error-reporter/
cat ~/.config/keboola-error-reporter/reported_errors.db
cat ~/.config/keboola-error-reporter/rate_limit.log
```

### Clearing State

```bash
# Clear deduplication cache
rm ~/.config/keboola-error-reporter/reported_errors.db

# Clear rate limit log
rm ~/.config/keboola-error-reporter/rate_limit.log

# Or clear everything
rm -rf ~/.config/keboola-error-reporter/
```

### Script Structure

```
error-reporter.sh
├── Configuration & Setup
├── Helper Functions (log, debug, etc.)
├── Validation Functions
│   ├── check_prerequisites()
│   └── validate_inputs()
├── Rate Limiting
│   ├── check_rate_limit()
│   └── record_report()
├── Deduplication
│   ├── compute_error_hash()
│   ├── check_duplicate()
│   └── record_error()
├── GitHub Issue Creation
│   ├── generate_issue_body()
│   ├── generate_issue_title()
│   ├── get_labels()
│   └── create_github_issue()
└── Main Function
```

### Contributing

To improve the error reporter:

1. Test changes with `--dry-run`
2. Add new features as functions
3. Update this README
4. Test with actual error scenarios
5. Verify rate limiting still works

### Integration Points

The error reporter can be integrated with:

- **Claude Code prompts**: Add instructions to call the script
- **Git hooks**: Run on failed tests or builds
- **CI/CD pipelines**: Report integration test failures
- **Monitoring tools**: Forward alerts to GitHub Issues
- **Custom wrappers**: Create project-specific reporters

## When to Report Errors

### DO Report

- API errors that aren't in documentation
- Outdated documentation
- Missing information in guides
- Unexpected behavior vs. documented behavior
- Common pitfalls not mentioned
- Confusing terminology

### DON'T Report

- User errors (wrong API key, etc.)
- Expected validation errors
- Rate limiting from Keboola API
- Network connectivity issues
- Your own code bugs (unless Keboola-related)

## License

This script is part of the Keboola Xmas Challenge project.

## Support

- **Issues**: Create a GitHub Issue (manually or via this tool!)
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check the [main README](../README.md)

---

**Happy Error Hunting!** May your issues be automatically triaged and your knowledge base forever growing.
