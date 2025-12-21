# Self-Healing Workflows Setup Guide

This guide will help you set up the self-healing GitHub Actions workflows for the Keboola AI knowledge base.

## Quick Start

### 1. Add Anthropic API Key

1. Get your API key from https://console.anthropic.com/settings/keys
2. Go to your repository Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your API key (starts with `sk-ant-...`)
6. Click "Add secret"

### 2. Enable Workflows

The workflows are already committed. GitHub Actions should automatically enable them.

To verify:
1. Go to the "Actions" tab in your repository
2. You should see three workflows listed:
   - Auto-Triage Issues
   - Validate Examples
   - Propose Fix

### 3. Test the System

#### Test 1: Validate Examples (Safe)

This workflow doesn't modify anything, just checks for issues:

```bash
# Via GitHub UI
1. Go to Actions → Validate Examples
2. Click "Run workflow"
3. Wait for completion
4. Check the results
```

#### Test 2: Auto-Triage (Creates labels)

This workflow analyzes issues and adds labels:

```bash
# Via GitHub UI
1. Go to Issues → New Issue
2. Choose "Auto-Report Issue" template
3. Fill in the details
4. Submit
5. Wait ~30 seconds
6. Check for auto-triage comment and labels
```

#### Test 3: Propose Fix (Creates PR)

This workflow creates pull requests:

```bash
# Option A: Triggered automatically by auto-triage (if confidence ≥ 80%)
1. Create an auto-report issue with clear, specific problem
2. Wait for auto-triage to run
3. If confidence is high, check for automatic PR

# Option B: Manual trigger
1. Go to Actions → Propose Fix
2. Click "Run workflow"
3. Enter an existing issue number and category
4. Click "Run workflow"
5. Wait for completion
6. Check for PR and issue comment
```

## Workflow Details

### Auto-Triage (auto-triage.yml)

- **Triggers:** When issue is created/labeled with "auto-report"
- **What it does:** Analyzes issue, categorizes, adds labels
- **API Usage:** ~500-1000 tokens per issue
- **Cost:** ~$0.003-$0.006 per issue (at current Claude pricing)

### Validate Examples (validate-examples.yml)

- **Triggers:** Daily at 2 AM UTC, on PR changes to .md files, manually
- **What it does:** Validates Python code syntax and documentation links
- **API Usage:** None (uses standard Python and requests)
- **Cost:** Free (no API calls)

### Propose Fix (propose-fix.yml)

- **Triggers:** Auto-triggered by auto-triage (≥80% confidence), manually
- **What it does:** Generates fix, creates PR with changes
- **API Usage:** ~2000-4000 tokens per fix
- **Cost:** ~$0.012-$0.024 per fix (at current Claude pricing)

## Expected Costs

Based on Claude Sonnet 4.5 pricing (December 2025):
- Input: ~$3/million tokens
- Output: ~$15/million tokens

**Estimated monthly costs for active repository:**
- 50 auto-report issues: ~$0.15-$0.30
- Daily validations: $0 (no API usage)
- 20 auto-fixes: ~$0.24-$0.48
- **Total: ~$0.40-$0.80/month**

For most repositories, this will be under $1/month.

## Security Best Practices

### API Key Security

- Never commit the API key to the repository
- Use GitHub Secrets for all sensitive data
- Rotate API keys periodically
- Monitor API usage in Anthropic console

### Workflow Permissions

The workflows use minimal required permissions:
- `issues: write` - To add labels and comments
- `contents: write` - To create branches and commits
- `pull-requests: write` - To create pull requests
- `contents: read` - To read repository files

### Branch Protection

Highly recommended to protect your main branch:

1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - Require a pull request before merging
   - Require approvals (at least 1)
   - Require status checks to pass
4. Save changes

This ensures all AI-generated changes are reviewed by humans.

## Monitoring

### Check Workflow Runs

1. Go to Actions tab
2. Click on a workflow to see run history
3. Click on a specific run to see logs
4. Check for failures or errors

### Review Generated PRs

All automated PRs have:
- Label: `automated-fix`
- Label: `needs-review`
- Clear description of changes
- Review checklist

**Never merge without reviewing!**

### Monitor API Usage

1. Go to https://console.anthropic.com
2. Check usage dashboard
3. Set up billing alerts if desired
4. Monitor for unexpected spikes

## Troubleshooting

### "API key not found" error

**Solution:** Make sure you've added the `ANTHROPIC_API_KEY` secret to your repository.

### Workflow doesn't trigger

**Solution:**
1. Check the issue has the "auto-report" label
2. Verify Actions are enabled in Settings
3. Check workflow run logs for errors

### Low confidence scores

**Solution:**
1. Provide more detailed issue descriptions
2. Include specific file paths and line numbers
3. Add error messages and reproduction steps
4. Reference related issues or documentation

### Fix proposals are incorrect

**Solution:**
1. Review and edit the PR before merging
2. Add feedback in PR comments
3. Consider adjusting the Claude prompt in propose-fix.yml
4. Lower confidence threshold to reduce auto-triggering

### Rate limiting

**Solution:**
1. Claude Sonnet 4.5 has high rate limits (2025)
2. Workflows include delays between API calls
3. If needed, add exponential backoff
4. Contact Anthropic support for tier upgrades

## Customization

### Adjust Confidence Threshold

Edit `.github/workflows/auto-triage.yml`:

```yaml
# Change this line (currently 80):
if: success() && steps.analyze.outputs.confidence >= 80
```

Lower values = more automated PRs (more review needed)
Higher values = fewer automated PRs (more manual fixes needed)

### Change Validation Schedule

Edit `.github/workflows/validate-examples.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # 2 AM UTC daily
```

Use https://crontab.guru to generate different schedules.

### Add More Categories

Edit the prompt in `.github/workflows/auto-triage.yml`:

```python
# Add new categories to this list:
category: One of "api-error", "outdated-docs", "pitfall", "your-new-category", "other"
```

And update the file selection logic in `propose-fix.yml`.

### Modify Fix Generation Prompt

Edit `.github/workflows/propose-fix.yml` to adjust how Claude generates fixes:

```python
# Look for the prompt variable and customize the guidelines
prompt = f"""You are an expert technical writer...

Guidelines:
1. Your custom guideline here
...
```

## Getting Help

- Check the workflow logs in the Actions tab
- Review the [workflows README](.github/workflows/README.md)
- Create an issue with the "help" label
- Consult the Anthropic documentation for API issues

## Next Steps

After setup:

1. Create a few test issues to verify the system works
2. Review and merge any generated PRs
3. Monitor for a week to ensure stability
4. Adjust confidence threshold based on accuracy
5. Document any customizations you make

## Success Metrics

Track these to measure effectiveness:

- Auto-triage accuracy rate (correct category)
- Percentage of high-confidence issues (≥80%)
- Auto-fix PR acceptance rate (merged vs closed)
- Time saved on documentation maintenance
- Reduction in duplicate issues
- Knowledge base quality improvements

The goal is 80%+ accuracy on all metrics.

---

Last updated: 2025-12-15
