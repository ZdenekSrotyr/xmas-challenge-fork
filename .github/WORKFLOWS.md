# GitHub Workflows Documentation

Complete guide to all GitHub Actions workflows in the learning system.

## Overview

The learning system uses GitHub Actions for automated processing of knowledge gaps, validation, and self-healing documentation updates.

## Workflows

### 1. Auto-merge Workflow

**File:** `.github/workflows/auto-merge.yml`

**Purpose:** Automatically merge safe, generated content PRs without manual intervention.

**Triggers:**
- PR opened by `github-actions[bot]`
- PR with `auto-merge` label
- Manual workflow dispatch

**Safety Criteria:**
1. PR title must start with `docs:`, `chore:`, or `style:`
2. Only changes files in `docs/`, `.github/`, or `*.md` files
3. All CI checks must pass
4. No code changes outside documentation

**How it works:**

```yaml
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: |
      github.event.pull_request.user.login == 'github-actions[bot]' ||
      contains(github.event.pull_request.labels.*.name, 'auto-merge')

    steps:
      - Check PR title format
      - Verify only safe files changed
      - Enable auto-merge with squash
      - Add explanatory comment
```

**Usage:**

```bash
# PRs from github-actions[bot] are automatically evaluated
# Or manually add label:
gh pr edit 123 --add-label "auto-merge"
```

**Configuration:**

```yaml
# Customize in workflow file:
SAFE_PATTERNS:
  - "^docs/"
  - "^\.github/"
  - ".*\.md$"

SAFE_PREFIXES:
  - "docs:"
  - "chore:"
  - "style:"
```

**Security:**

- Requires `contents: write` permission
- Only works for bot-created PRs or labeled PRs
- Human review required before merge (auto-merge queues, doesn't force)
- All checks must pass

**Example Output:**

```
✅ Auto-merge enabled for generated content PR.
Will merge automatically when all checks pass.

Safety checks passed:
- PR from github-actions[bot]
- Title: docs: Update Storage API authentication
- Files changed: docs/storage-api.md, README.md
- All files in safe directories
```

### 2. Learn from Interaction Workflow

**File:** `.github/workflows/learn-from-interaction.yml`

**Purpose:** Process captured interactions to identify knowledge gaps and create improvement issues.

**Triggers:**
- Manual workflow dispatch with interaction ID

**How it works:**

```yaml
on:
  workflow_dispatch:
    inputs:
      interaction_id:
        description: 'Interaction ID to analyze'
        required: true
        type: number

jobs:
  analyze:
    steps:
      - Checkout repository
      - Set up Python 3.11
      - Run analyzer.py on interaction
      - Get pending learnings
      - Create GitHub issues (TODO)
```

**Usage:**

```bash
# Trigger analysis for specific interaction
gh workflow run learn-from-interaction.yml \
    -f interaction_id=42

# View workflow run
gh run list --workflow=learn-from-interaction.yml

# View logs
gh run view --log
```

**Environment Variables:**

```yaml
# Required in GitHub secrets:
ANTHROPIC_API_KEY: "sk-ant-..."

# Optional:
GITHUB_TOKEN: Automatically provided
```

**Expected Output:**

```
Analyzing interaction #42...
✅ Identified gap: Storage API authentication
Gap type: missing_info
Proposed fix: Add section about authentication methods

Pending learnings:
Learning #1: Storage API - Add authentication examples
Learning #2: Job polling - Clarify timeout behavior
Learning #3: Input mapping - Add visual diagram

Would create issues here
```

**Customization:**

```yaml
# Modify analyzer behavior:
- name: Analyze interaction
  env:
    CONFIDENCE_THRESHOLD: 0.8
    MAX_RETRIES: 3
    TIMEOUT: 30
  run: |
    cd automation/learning
    python analyzer.py \
      --interaction-id ${{ inputs.interaction_id }} \
      --confidence-threshold ${{ env.CONFIDENCE_THRESHOLD }}
```

## Workflow Dependencies

### Required Secrets

Set up in GitHub repository settings:

```bash
# Required for AI analysis
gh secret set ANTHROPIC_API_KEY

# Optional: Custom GitHub token with more permissions
gh secret set CUSTOM_GITHUB_TOKEN
```

### Required Permissions

In workflow files:

```yaml
permissions:
  contents: write      # For auto-merge and creating commits
  pull-requests: write # For PR operations
  issues: write        # For creating issues (future)
```

### Required Files

Directory structure:

```
.github/
├── workflows/
│   ├── auto-merge.yml
│   └── learn-from-interaction.yml
└── ISSUE_TEMPLATE/
    ├── auto-report.yml
    └── config.yml

automation/
└── learning/
    ├── capture.py
    ├── analyzer.py
    ├── proposer.py
    ├── feedback.py
    └── data/
        └── memory.db
```

## Workflow Patterns

### Pattern 1: Safe Auto-merge

For documentation-only changes:

```yaml
name: Auto-merge Safe Changes

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'docs/**'
      - '**.md'
      - '.github/**'

jobs:
  auto-merge:
    if: github.actor == 'github-actions[bot]'
    steps:
      - name: Enable auto-merge
        run: gh pr merge ${{ github.event.pull_request.number }} --auto --squash
```

### Pattern 2: AI-Powered Analysis

For knowledge gap identification:

```yaml
name: Analyze Interaction

on:
  workflow_dispatch:
    inputs:
      interaction_id:
        type: number

jobs:
  analyze:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Analyze with Claude
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python automation/learning/analyzer.py \
            --interaction-id ${{ inputs.interaction_id }}
```

### Pattern 3: Batch Processing

For processing multiple interactions:

```yaml
name: Batch Analyze

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2am

jobs:
  batch-analyze:
    steps:
      - name: Get unanalyzed interactions
        id: interactions
        run: |
          IDS=$(sqlite3 automation/learning/data/memory.db \
            "SELECT id FROM interactions WHERE identified_gap = 0 LIMIT 100;")
          echo "ids=$IDS" >> $GITHUB_OUTPUT

      - name: Analyze batch
        run: |
          for id in ${{ steps.interactions.outputs.ids }}; do
            python automation/learning/analyzer.py --interaction-id $id
          done
```

## Testing Workflows

### Local Testing

Use [act](https://github.com/nektos/act) to test workflows locally:

```bash
# Install act
brew install act

# Test auto-merge workflow
act pull_request -W .github/workflows/auto-merge.yml

# Test learn workflow with input
act workflow_dispatch \
  -W .github/workflows/learn-from-interaction.yml \
  -j analyze \
  --input interaction_id=42
```

### Dry-run Testing

Add dry-run mode to workflows:

```yaml
- name: Analyze (dry-run)
  if: inputs.dry_run == true
  run: |
    echo "Would analyze interaction ${{ inputs.interaction_id }}"
    python analyzer.py --interaction-id ${{ inputs.interaction_id }} --dry-run
```

### Manual Trigger Testing

Test workflows manually:

```bash
# Trigger learn workflow
gh workflow run learn-from-interaction.yml \
  -f interaction_id=1

# View results
gh run list --workflow=learn-from-interaction.yml --limit 1
gh run view --log
```

## Monitoring Workflows

### View Recent Runs

```bash
# All workflows
gh run list --limit 10

# Specific workflow
gh run list --workflow=auto-merge.yml --limit 5

# Failed runs only
gh run list --status=failure
```

### View Logs

```bash
# Latest run
gh run view --log

# Specific run
gh run view 123456789 --log

# Specific job
gh run view 123456789 --log --job=analyze
```

### Set Up Notifications

Configure in `.github/workflows/`:

```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Workflow failed: ${{ github.workflow }}',
        body: 'Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}',
        labels: ['workflow-failure']
      })
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied

```
Error: Resource not accessible by integration
```

**Fix:** Add required permissions to workflow:

```yaml
permissions:
  contents: write
  pull-requests: write
```

#### 2. API Key Not Found

```
Error: ANTHROPIC_API_KEY not set
```

**Fix:** Add secret to repository:

```bash
gh secret set ANTHROPIC_API_KEY
```

#### 3. Database Not Found

```
Error: unable to open database file
```

**Fix:** Initialize database first:

```yaml
- name: Initialize database
  run: |
    mkdir -p automation/learning/data
    python automation/learning/capture.py --context "init" --response "init"
```

#### 4. Workflow Not Triggering

**Check:**
1. Workflow file syntax: `yamllint .github/workflows/auto-merge.yml`
2. Trigger conditions: Review `on:` section
3. Branch protection rules: May block auto-merge
4. Repository permissions: Workflow needs access

**Debug:**
```yaml
- name: Debug info
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Actor: ${{ github.actor }}"
    echo "Ref: ${{ github.ref }}"
```

### Debugging Workflows

Add debug output:

```yaml
- name: Debug workflow
  env:
    DEBUG: true
  run: |
    set -x  # Enable command tracing
    echo "::debug::Current directory: $(pwd)"
    echo "::debug::Environment: $(env | sort)"
    ls -la automation/learning/
```

Use job summaries:

```yaml
- name: Create summary
  run: |
    echo "## Analysis Results" >> $GITHUB_STEP_SUMMARY
    echo "- Interaction ID: ${{ inputs.interaction_id }}" >> $GITHUB_STEP_SUMMARY
    echo "- Status: Success" >> $GITHUB_STEP_SUMMARY
```

## Performance Optimization

### Caching

Cache Python dependencies:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

- name: Install dependencies
  run: pip install -r requirements.txt
```

Cache database between runs:

```yaml
- name: Cache database
  uses: actions/cache@v4
  with:
    path: automation/learning/data/memory.db
    key: learning-db-${{ github.sha }}
    restore-keys: learning-db-
```

### Parallel Jobs

Run analyses in parallel:

```yaml
jobs:
  get-interactions:
    outputs:
      matrix: ${{ steps.ids.outputs.matrix }}
    steps:
      - id: ids
        run: |
          IDS=$(sqlite3 db "SELECT json_group_array(id) FROM interactions LIMIT 10;")
          echo "matrix={\"id\":$IDS}" >> $GITHUB_OUTPUT

  analyze:
    needs: get-interactions
    strategy:
      matrix: ${{ fromJson(needs.get-interactions.outputs.matrix) }}
    steps:
      - run: python analyzer.py --interaction-id ${{ matrix.id }}
```

### Conditional Execution

Skip unnecessary steps:

```yaml
- name: Check if analysis needed
  id: check
  run: |
    COUNT=$(sqlite3 db "SELECT COUNT(*) FROM interactions WHERE identified_gap = 0;")
    echo "count=$COUNT" >> $GITHUB_OUTPUT

- name: Analyze
  if: steps.check.outputs.count > 0
  run: python analyzer.py
```

## Security Best Practices

### Secret Management

```yaml
# ✅ Good: Use secrets
- env:
    API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

# ❌ Bad: Hardcode secrets
- env:
    API_KEY: sk-ant-hardcoded-key
```

### Input Validation

```yaml
- name: Validate input
  run: |
    if ! [[ "${{ inputs.interaction_id }}" =~ ^[0-9]+$ ]]; then
      echo "Error: Invalid interaction ID"
      exit 1
    fi
```

### Least Privilege

```yaml
# ✅ Good: Minimal permissions
permissions:
  contents: read
  pull-requests: write

# ❌ Bad: Excessive permissions
permissions:
  contents: write
  pull-requests: write
  issues: write
  packages: write
```

### Output Sanitization

```yaml
- name: Safe output
  run: |
    RESULT=$(python analyzer.py 2>&1 | head -100)  # Limit output
    echo "::debug::$RESULT"  # Use debug log level
```

## Advanced Patterns

### Dynamic Matrix

Generate test matrix dynamically:

```yaml
jobs:
  setup:
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - id: set-matrix
        run: |
          CONCEPTS=$(sqlite3 db "SELECT DISTINCT concept FROM learnings;")
          MATRIX=$(echo "$CONCEPTS" | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "matrix=$MATRIX" >> $GITHUB_OUTPUT

  process:
    needs: setup
    strategy:
      matrix:
        concept: ${{ fromJson(needs.setup.outputs.matrix) }}
    steps:
      - run: echo "Processing ${{ matrix.concept }}"
```

### Workflow Chaining

Chain multiple workflows:

```yaml
# Workflow 1: Capture
name: Capture Interaction
on: [workflow_dispatch]
jobs:
  capture:
    outputs:
      interaction_id: ${{ steps.capture.outputs.id }}
    steps:
      - id: capture
        run: |
          ID=$(python capture.py)
          echo "id=$ID" >> $GITHUB_OUTPUT

      - name: Trigger analysis
        run: |
          gh workflow run learn-from-interaction.yml \
            -f interaction_id=${{ steps.capture.outputs.id }}
```

### Custom Actions

Create reusable action:

```yaml
# .github/actions/analyze-interaction/action.yml
name: 'Analyze Interaction'
description: 'Analyze a captured interaction for knowledge gaps'
inputs:
  interaction-id:
    description: 'Interaction ID to analyze'
    required: true
runs:
  using: 'composite'
  steps:
    - run: python automation/learning/analyzer.py --interaction-id ${{ inputs.interaction-id }}
      shell: bash

# Use in workflow:
- uses: ./.github/actions/analyze-interaction
  with:
    interaction-id: 42
```

## Cost Optimization

### Minimize API Calls

```yaml
- name: Batch analyze
  run: |
    # Analyze multiple interactions in one API call
    python analyzer.py --batch --interaction-ids 1,2,3,4,5
```

### Use Smaller Models for Simple Tasks

```yaml
- name: Simple triage
  env:
    MODEL: claude-3-haiku-20240307  # Cheaper model
  run: python analyzer.py --model ${{ env.MODEL }}
```

### Cache Results

```yaml
- name: Check cache
  id: cache
  uses: actions/cache@v4
  with:
    path: automation/learning/cache/
    key: analysis-${{ hashFiles('automation/learning/data/memory.db') }}

- name: Analyze
  if: steps.cache.outputs.cache-hit != 'true'
  run: python analyzer.py
```

## Metrics & Reporting

### Track Workflow Success

```yaml
- name: Record metrics
  if: always()
  run: |
    STATUS=${{ job.status }}
    DURATION=${{ job.duration }}
    echo "${{ github.run_id }},$STATUS,$DURATION" >> metrics/workflows.csv
```

### Generate Reports

```yaml
- name: Generate report
  run: |
    echo "# Workflow Report" > report.md
    echo "- Date: $(date)" >> report.md
    echo "- Status: ${{ job.status }}" >> report.md
    echo "- Analyzed: $(sqlite3 db 'SELECT COUNT(*) FROM learnings;')" >> report.md

- name: Upload report
  uses: actions/upload-artifact@v4
  with:
    name: workflow-report
    path: report.md
```

## Conclusion

These workflows provide a complete self-improving system:

1. **Auto-merge** handles safe documentation updates automatically
2. **Learn from Interaction** identifies knowledge gaps and proposes fixes
3. **Human oversight** ensures quality and safety
4. **Continuous improvement** through automated analysis and updates

For questions or issues, see the [main README](../automation/learning/README.md) or open a GitHub issue.

---

Last updated: 2025-12-16
