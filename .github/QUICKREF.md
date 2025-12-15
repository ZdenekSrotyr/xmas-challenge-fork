# Self-Healing Workflows - Quick Reference

## TL;DR

1. Add `ANTHROPIC_API_KEY` to repository secrets
2. Create issue with "auto-report" label
3. Wait for automatic triage and fix proposal
4. Review and merge the PR
5. Knowledge base is updated!

---

## Common Tasks

### Report an Issue

```bash
# Via GitHub UI
1. Issues → New Issue → Auto-Report Issue
2. Fill in the template
3. Submit
4. Check back in ~1 minute for triage results
```

### Manually Trigger Fix

```bash
# Via GitHub CLI
gh workflow run propose-fix.yml \
  -f issue_number=42 \
  -f category=api-error
```

### Check Validation Results

```bash
# Via GitHub CLI
gh run list --workflow=validate-examples.yml
gh run view <run-id>
```

### Download Validation Report

```bash
# Via GitHub CLI
gh run download <run-id> --name validation-results
```

---

## Workflow Cheat Sheet

| Workflow | Trigger | What It Does | Cost |
|----------|---------|--------------|------|
| **auto-triage** | Issue with "auto-report" label | Analyzes and categorizes | ~$0.005 |
| **validate-examples** | Daily 2 AM UTC, PRs | Checks syntax and links | $0 |
| **propose-fix** | Auto (≥80% confidence) or manual | Creates PR with fix | ~$0.018 |

---

## Issue Categories

- **api-error**: Wrong API endpoint, authentication, or calls
- **outdated-docs**: Documentation references deprecated features
- **pitfall**: Common mistake that should be documented
- **other**: Everything else

---

## Confidence Scores

- **≥80%**: High confidence → Auto-generates fix PR
- **60-79%**: Medium confidence → Manual review needed
- **<60%**: Low confidence → Human investigation required

---

## Labels Guide

### Automatically Added

- `category:*` - The issue category
- `priority:*` - high/medium/low
- `confidence:*` - The confidence score
- `automated-fix` - PR was automatically generated
- `needs-review` - Requires human review

### Manual Labels

- `needs-manual-fix` - Automation failed, need human
- `triage-failed` - Triage workflow error
- `validation-failure` - Daily validation found issues

---

## PR Review Checklist

When reviewing automated PRs:

- [ ] Read the analysis - does it make sense?
- [ ] Check each changed file
- [ ] Verify code examples work
- [ ] Test any code snippets locally
- [ ] Check links are valid and correct
- [ ] Ensure style is consistent
- [ ] Look for unintended side effects
- [ ] Approve or request changes

**Never merge without reviewing!**

---

## Common Commands

### Check Workflow Status

```bash
# List recent runs
gh run list

# Watch a specific run
gh run watch <run-id>

# View logs
gh run view <run-id> --log
```

### Manage Issues

```bash
# Create auto-report issue
gh issue create --label auto-report --title "API auth broken" --body "..."

# View issue with labels
gh issue view 42

# Add label manually
gh issue edit 42 --add-label "needs-review"
```

### Work with PRs

```bash
# List automated PRs
gh pr list --label automated-fix

# Review PR
gh pr view 123
gh pr checkout 123
gh pr review 123 --approve
gh pr merge 123
```

---

## Debugging

### Workflow Won't Trigger

```bash
# Check if Actions are enabled
gh api repos/:owner/:repo/actions/permissions

# View workflow file
gh workflow view auto-triage.yml

# Check for syntax errors
yamllint .github/workflows/auto-triage.yml
```

### API Key Issues

```bash
# Verify secret exists (won't show value)
gh secret list

# Update secret
gh secret set ANTHROPIC_API_KEY < key.txt
```

### Workflow Failures

```bash
# Get failure logs
gh run view <run-id> --log-failed

# Rerun failed jobs
gh run rerun <run-id> --failed
```

---

## Cost Estimates

### Claude API (Sonnet 4.5 - Dec 2025)

- Input: ~$3/million tokens
- Output: ~$15/million tokens

### Per Operation

- Triage: ~1000 tokens → $0.005
- Fix: ~4000 tokens → $0.018
- Validation: 0 tokens → $0

### Monthly (Typical)

- 50 issues triaged: $0.25
- 20 fixes generated: $0.36
- 30 validations: $0
- **Total: ~$0.61/month**

---

## File Locations

```
.github/
├── workflows/
│   ├── auto-triage.yml          # Issue triage workflow
│   ├── validate-examples.yml    # Daily validation
│   ├── propose-fix.yml          # Fix generation
│   └── README.md                # Detailed documentation
├── ISSUE_TEMPLATE/
│   ├── auto-report.yml          # Issue template
│   └── config.yml               # Template configuration
├── ARCHITECTURE.md              # System architecture
├── SETUP.md                     # Setup instructions
└── QUICKREF.md                  # This file
```

---

## Environment Variables

### In Workflows

- `ANTHROPIC_API_KEY`: Claude API key (required for triage & fix)
- `GITHUB_TOKEN`: Auto-provided by GitHub Actions

### For Local Testing

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."
```

---

## API Limits (2025)

### Anthropic (Tier 1)

- 50 requests/minute
- 40,000 tokens/minute
- Typical workflow uses 1 request, ~4000 tokens

### GitHub Actions

- 1,000 API requests/hour
- Unlimited workflow runs (public repos)
- 2,000 minutes/month (private repos free tier)

---

## Tips and Tricks

### Get Better Triage Results

1. Use clear, specific issue titles
2. Include error messages
3. Mention specific file paths
4. Add reproduction steps
5. Link to related issues

### Reduce False Positives

1. Lower confidence threshold (in auto-triage.yml)
2. Improve category descriptions in prompt
3. Add more context to issue template
4. Review and provide feedback on PRs

### Speed Up Workflows

1. Cache Python dependencies (already enabled)
2. Limit file scanning to changed files
3. Use shallow clones (already using fetch-depth: 0 where needed)
4. Run validation only on affected files

---

## Support

- **Workflow issues**: Check `.github/workflows/README.md`
- **Setup problems**: Check `.github/SETUP.md`
- **Architecture questions**: Check `.github/ARCHITECTURE.md`
- **GitHub Actions**: https://docs.github.com/actions
- **Claude API**: https://docs.anthropic.com

---

## Quick Links

- [Actions Tab](../../actions)
- [Issues](../../issues)
- [Pull Requests](../../pulls)
- [Anthropic Console](https://console.anthropic.com)
- [GitHub Secrets](../../settings/secrets/actions)

---

**Version:** 1.0 | **Last Updated:** 2025-12-15

For detailed information, see the full documentation in `.github/workflows/README.md`
