# Self-Healing Workflows Architecture

## Overview

The self-healing system consists of three interconnected GitHub Actions workflows that automate the maintenance and improvement of the Keboola AI knowledge base.

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REPORTS ISSUE                           │
│              (via auto-report issue template)                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Issue created with "auto-report" label
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO-TRIAGE.YML                              │
│                                                                 │
│  1. Fetch issue details from GitHub API                        │
│  2. Call Claude API with issue content                         │
│  3. Claude analyzes and returns:                               │
│     - Category (api-error, outdated-docs, pitfall, other)      │
│     - Confidence score (0-100%)                                │
│     - Priority (high, medium, low)                             │
│     - Recommended labels                                       │
│     - Reasoning                                                │
│  4. Add labels to issue                                        │
│  5. Post analysis comment                                      │
│  6. If confidence ≥ 80%:                                       │
│     ↓ Trigger propose-fix workflow                            │
│                                                                 │
└────┬────────────────────────────────────────────┬──────────────┘
     │                                            │
     │ confidence < 80%                           │ confidence ≥ 80%
     │                                            │
     ▼                                            ▼
┌─────────────────────┐              ┌─────────────────────────────┐
│  MANUAL REVIEW      │              │    PROPOSE-FIX.YML          │
│  Label: needs-review│              │                             │
└─────────────────────┘              │  1. Fetch issue details     │
                                     │  2. Find relevant files     │
                                     │     based on category:      │
                                     │     - api-error: API files  │
                                     │     - outdated-docs: SKILL  │
                                     │     - pitfall: guides       │
                                     │  3. Read current content    │
                                     │  4. Call Claude API with:   │
                                     │     - Issue description     │
                                     │     - Current file content  │
                                     │     - Fix guidelines        │
                                     │  5. Claude generates:       │
                                     │     - Analysis              │
                                     │     - Specific changes      │
                                     │     - PR title & desc       │
                                     │  6. Apply changes to files  │
                                     │  7. Create git branch       │
                                     │  8. Commit changes          │
                                     │  9. Create Pull Request     │
                                     │ 10. Comment on issue        │
                                     │                             │
                                     └──────────┬──────────────────┘
                                                │
                                                ▼
                                     ┌──────────────────────────────┐
                                     │   PULL REQUEST CREATED       │
                                     │   Labels:                    │
                                     │   - automated-fix            │
                                     │   - needs-review             │
                                     │   - category:*               │
                                     └──────────┬───────────────────┘
                                                │
                                                ▼
                                     ┌──────────────────────────────┐
                                     │   HUMAN REVIEW               │
                                     │   Checklist:                 │
                                     │   [ ] Verify accuracy        │
                                     │   [ ] Test code examples     │
                                     │   [ ] Check links            │
                                     │   [ ] Validate style         │
                                     └──────────┬───────────────────┘
                                                │
                                                ▼
                                     ┌──────────────────────────────┐
                                     │   MERGE TO MAIN              │
                                     │   Knowledge base updated!    │
                                     └──────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATE-EXAMPLES.YML                        │
│                    (Runs independently)                         │
│                                                                 │
│  Triggers:                                                      │
│  - Schedule: Daily at 2 AM UTC                                 │
│  - Pull Request: On changes to .md files                       │
│  - Manual: workflow_dispatch                                   │
│                                                                 │
│  Steps:                                                         │
│  1. Find all SKILL.md files                                    │
│  2. Extract Python code blocks                                 │
│  3. Validate syntax with ast.parse()                           │
│  4. Extract Keboola documentation links                        │
│  5. Check each link (HTTP HEAD/GET)                            │
│  6. Generate validation report                                 │
│  7. On PR: Comment with results                                │
│  8. On schedule (if failures):                                 │
│     Create auto-report issue ──────────┐                       │
│                                         │                       │
└─────────────────────────────────────────┼───────────────────────┘
                                          │
                                          │ Creates issue with
                                          │ "auto-report" label
                                          │
                                          └──────► Triggers auto-triage
                                                  (back to start)
```

## Component Details

### 1. Auto-Triage Workflow

**File:** `.github/workflows/auto-triage.yml`

**Inputs:**
- GitHub issue with "auto-report" label

**Outputs:**
- Labels added to issue
- Analysis comment on issue
- Workflow dispatch to propose-fix (if high confidence)

**Key Technologies:**
- Python 3.11
- Anthropic Python SDK
- Claude Sonnet 4.5 model (claude-sonnet-4-5-20250929)
- GitHub Actions (actions/checkout@v4, actions/setup-python@v5, actions/github-script@v7)

**API Usage:**
- Single Claude API call per issue
- ~500-1000 input tokens
- ~200-400 output tokens
- Cost: ~$0.003-$0.006 per issue

**Error Handling:**
- JSON parsing validation
- Required fields check
- Failure creates "triage-failed" label
- Posts error comment on issue

---

### 2. Validate Examples Workflow

**File:** `.github/workflows/validate-examples.yml`

**Inputs:**
- Schedule (cron: daily 2 AM UTC)
- Pull request changes to .md files
- Manual trigger

**Outputs:**
- Validation report artifact
- PR comment (if on PR)
- Auto-report issue (if scheduled run fails)

**Key Technologies:**
- Python 3.11
- ast (Abstract Syntax Trees) for Python validation
- requests library for link checking
- No AI/API calls (pure validation)

**Validation Checks:**
1. **Python Syntax:**
   - Extract code from ```python blocks
   - Parse with ast.parse()
   - Skip templates (containing ..., TODO, PLACEHOLDER)
   - Report line-level syntax errors

2. **Link Validation:**
   - Extract markdown links [text](url)
   - Filter Keboola domains (developers.keboola.com, help.keboola.com, etc.)
   - HTTP HEAD/GET requests
   - Handle redirects and retries
   - Report broken links (404, 500+, timeout)

**Error Handling:**
- Continue on individual failures
- Aggregate all errors in report
- Upload artifacts for review
- Rate limiting (0.5s between requests)

---

### 3. Propose Fix Workflow

**File:** `.github/workflows/propose-fix.yml`

**Inputs:**
- issue_number (string)
- category (string: api-error, outdated-docs, pitfall, other)

**Outputs:**
- Git branch with changes
- Pull request
- Comment on original issue
- Fix proposal artifact

**Key Technologies:**
- Python 3.11
- Anthropic Python SDK
- Claude Sonnet 4.5 model
- Git (branch creation, commits, push)
- GitHub Actions

**Processing Steps:**

1. **File Discovery:**
   - Parse issue body for mentioned files
   - Category-based file selection:
     - api-error: Files with "api", "client", "authentication"
     - outdated-docs: All SKILL.md files
     - pitfall: Files with "pitfall", "common mistakes"
   - Limit to top 5 most relevant files

2. **Fix Generation:**
   - Read current content of target files
   - Build context with file contents
   - Call Claude with:
     - Issue details
     - Current documentation
     - Fix guidelines
     - Category-specific instructions
   - Parse JSON response with changes

3. **Change Application:**
   - For each proposed change:
     - If "current" text specified: replace it
     - If section specified: insert into section
     - Otherwise: append to end
   - Write modified files
   - Track files changed

4. **PR Creation:**
   - Create branch: `fix/issue-{number}-{timestamp}`
   - Commit with proper attribution
   - Push to origin
   - Create PR with:
     - AI-generated title and description
     - Detailed change breakdown
     - Review checklist
     - Labels: automated-fix, needs-review, category:*

**API Usage:**
- Single Claude API call per fix
- ~2000-3000 input tokens (includes file content)
- ~800-1500 output tokens (includes changes)
- Cost: ~$0.012-$0.024 per fix

**Error Handling:**
- JSON parsing validation
- File existence checks
- Git operation error handling
- Failure creates "needs-manual-fix" label
- Posts error comment on issue

---

## Data Flow

### Issue Metadata Flow

```
Issue Created
    ↓
   title: string
   body: string
   labels: ["auto-report"]
    ↓
Auto-Triage
    ↓
   category: string
   confidence: 0-100
   priority: string
   labels: ["category:*", "priority:*", "confidence:*"]
    ↓
Propose Fix
    ↓
   changes: [
     {file, section, current, proposed, reasoning}
   ]
   pr_title: string
   pr_description: string
    ↓
Pull Request
    ↓
   branch: string
   files_changed: [string]
   labels: ["automated-fix", "needs-review"]
```

### Validation Flow

```
Scheduled Trigger / PR Trigger
    ↓
Find SKILL.md files
    ↓
Extract code blocks: [string]
Extract links: [(text, url)]
    ↓
Validate Python syntax
Check link accessibility
    ↓
Aggregate results:
  - total_examples
  - valid_examples
  - invalid_examples
  - total_links
  - valid_links
  - broken_links
    ↓
Generate report markdown
    ↓
Post comment (PR) / Create issue (schedule)
Upload artifacts
```

## Security Model

### Secrets Used

- `ANTHROPIC_API_KEY`: Claude API authentication
  - Scope: Repository secret
  - Access: Read-only by workflows
  - Rotation: Recommended quarterly

- `GITHUB_TOKEN`: Automatic token
  - Scope: Provided by GitHub Actions
  - Permissions: issues:write, contents:write, pull-requests:write
  - Lifetime: Single workflow run

### Permission Model

All workflows use minimal required permissions:

```yaml
permissions:
  issues: write        # Add labels, create comments
  contents: write      # Create branches, push commits (propose-fix only)
  contents: read       # Read files (auto-triage, validate-examples)
  pull-requests: write # Create PRs (propose-fix only)
```

### Input Validation

1. **Auto-Triage:**
   - Issue title/body: Escaped in Python heredoc
   - JSON parsing: Strict validation with error handling
   - Label names: Validated against allowed categories

2. **Validate-Examples:**
   - File paths: Restricted to repository root
   - URLs: Validated URL format
   - Code: Never executed, only parsed

3. **Propose-Fix:**
   - Issue number: Validated as integer
   - Category: Enum validation
   - File paths: Checked for existence before writing
   - Branch names: Sanitized (alphanumeric + hyphens)

## Scalability Considerations

### API Rate Limits

**Anthropic Claude API (2025):**
- Tier 1: 50 requests/minute, 40,000 tokens/minute
- Tier 2: 1,000 requests/minute, 80,000 tokens/minute
- Tier 3: 2,000 requests/minute, 160,000 tokens/minute

**GitHub API:**
- Actions workflows: 1,000 requests/hour
- Built-in throttling and retries

### Workflow Concurrency

```yaml
# Auto-triage: One per issue
concurrency:
  group: auto-triage-${{ github.event.issue.number }}
  cancel-in-progress: false

# Validate-examples: One per branch
concurrency:
  group: validate-examples-${{ github.ref }}
  cancel-in-progress: true

# Propose-fix: One per issue
concurrency:
  group: propose-fix-${{ github.event.inputs.issue_number }}
  cancel-in-progress: false
```

### Cost Scaling

For a repository with:
- 50 issues/month
- Daily validation runs
- 20 automated fixes/month

**Monthly costs:**
- Auto-triage: 50 × $0.005 = $0.25
- Validation: 30 × $0 = $0
- Propose-fix: 20 × $0.018 = $0.36
- **Total: ~$0.61/month**

For high-volume repositories (200+ issues/month):
- Estimated cost: ~$2-3/month
- Still negligible compared to developer time saved

## Failure Modes and Recovery

### Workflow Failures

| Failure | Detection | Recovery | Prevention |
|---------|-----------|----------|------------|
| API timeout | 10s timeout in requests | Retry with exponential backoff | None needed (rare) |
| Invalid JSON | JSON parsing error | Label "triage-failed", comment | Improve Claude prompt |
| File not found | os.path.exists check | Skip file, continue | Better file discovery |
| Git conflict | Git command error | Comment on issue, exit | Branch per issue |
| Rate limit | 429 HTTP status | Wait and retry | Track usage, add delays |

### Data Quality Issues

| Issue | Detection | Recovery | Prevention |
|-------|-----------|----------|------------|
| Low confidence | Confidence < 80% | Manual review label | Better issue templates |
| Wrong category | Human review | Edit labels, re-trigger | Improve triage prompt |
| Bad fix | PR review fails | Edit PR, don't merge | Better fix generation prompt |
| Broken code | Validation workflow | PR blocks merge | Add pre-commit validation |

## Monitoring and Observability

### Key Metrics to Track

1. **Triage Accuracy:**
   - % correct category assignments
   - Average confidence score
   - % high confidence (≥80%)

2. **Fix Quality:**
   - % PRs merged vs closed
   - Average review time
   - Number of revisions needed

3. **System Health:**
   - Workflow success rate
   - API error rate
   - Average execution time

4. **Business Value:**
   - Issues triaged automatically
   - Developer time saved
   - Knowledge base improvements/week

### Logging

All workflows include verbose logging:
- Step-by-step progress
- API request/response summaries
- File operations
- Error details with stack traces

Access logs:
1. Go to Actions tab
2. Select workflow run
3. Click on job
4. Expand step to see logs

### Artifacts

Workflows save artifacts for debugging:
- `validation_report.md`: Full validation results (30 days)
- `validation_errors.txt`: Python syntax errors (30 days)
- `broken_links.txt`: Broken documentation links (30 days)
- `fix_proposal.json`: Complete fix proposal (30 days)

Download artifacts:
1. Go to workflow run
2. Scroll to "Artifacts" section
3. Click to download

## Future Enhancements

### Phase 2: Machine Learning

- Track triage accuracy over time
- Build dataset of (issue, correct_category) pairs
- Fine-tune category classification
- Adjust confidence scoring based on outcomes

### Phase 3: Advanced Fixes

- Multi-file coordinated changes
- Update cross-references automatically
- Maintain consistency across documentation
- Handle complex refactoring

### Phase 4: Testing Automation

- Spin up sandbox environment
- Run code examples automatically
- Validate screenshots
- Check rendering of markdown

### Phase 5: Notifications

- Slack/Discord integration
- Weekly summary reports
- Critical issue alerts
- Validation failure notifications

## Architecture Principles

1. **Fail Gracefully:** Each workflow handles errors independently
2. **Idempotent:** Re-running workflows produces same result
3. **Auditable:** All changes traceable via Git and GitHub
4. **Secure:** Minimal permissions, secret management
5. **Cost-Effective:** Optimize API usage, cache when possible
6. **Human-in-Loop:** Always require review for automated changes
7. **Observable:** Comprehensive logging and artifacts
8. **Maintainable:** Clear code, extensive documentation

## Technology Stack

### Core Technologies

- **GitHub Actions:** Workflow orchestration
- **Python 3.11:** Primary language
- **Claude Sonnet 4.5:** AI analysis and generation
- **Git:** Version control
- **Markdown:** Documentation format

### Python Libraries

- `anthropic`: Claude API client
- `pyyaml`: YAML parsing (for frontmatter)
- `requests`: HTTP requests (link checking)
- `ast`: Python syntax validation
- `json`: JSON parsing
- `pathlib`: File path operations
- `re`: Regular expressions

### GitHub Actions

- `actions/checkout@v4`: Repository checkout
- `actions/setup-python@v5`: Python environment setup
- `actions/github-script@v7`: GitHub API interactions
- `actions/upload-artifact@v4`: Artifact management

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Anthropic API Documentation](https://docs.anthropic.com)
- [Python ast module](https://docs.python.org/3/library/ast.html)
- [Workflow Setup Guide](SETUP.md)
- [Workflow Details](workflows/README.md)

---

**Architecture Version:** 1.0
**Last Updated:** 2025-12-15
**Model Used:** Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
