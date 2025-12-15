# Metrics Tracking System

Comprehensive metrics tracking and visualization for the self-healing knowledge base system.

## Overview

This metrics system tracks and analyzes key performance indicators (KPIs) to measure the effectiveness of the self-healing knowledge base:

- **Triage Accuracy**: Target 80%+ - How accurately issues are triaged
- **High-Confidence Issues**: Target 50%+ - Percentage of issues with high confidence scores
- **PR Merge Rate**: Target 70%+ - Success rate of automated pull requests
- **Time Saved**: Target 15+ hours/month - Developer time saved by automation
- **Error Trends**: Track and reduce errors over time

## Components

### 1. track-usage.py

Tracks usage statistics for the knowledge base system.

**What it tracks:**
- Plugin usage (which plugins are invoked and how often)
- Skill triggers (which skills are being used)
- Error reporter usage (how often errors are reported)
- Daily and hourly usage patterns
- Usage trends over time

**Usage:**

```bash
# Parse log file
python track-usage.py --log-file path/to/claude-usage.log --output-dir ./metrics-output

# Generate simulated data for testing
python track-usage.py --simulate --days 30

# Custom output files
python track-usage.py --simulate --json-output my-stats.json --csv-output my-stats.csv
```

**Outputs:**
- `usage-stats.json` - Complete statistics in JSON format
- `usage-stats.csv` - Summary statistics in CSV format
- `daily-usage.csv` - Daily usage counts
- Terminal summary with visualization

### 2. track-errors.py

Tracks and analyzes error statistics over time.

**What it tracks:**
- Errors by type, severity, and category
- Error resolution rates and times
- Error trends (increasing/decreasing)
- Daily error counts
- Resolution time by severity

**Usage:**

```bash
# Parse error log
python track-errors.py --error-log path/to/errors.json --output-dir ./metrics-output

# Generate simulated data
python track-errors.py --simulate --days 30 --errors-per-day 5

# Analyze existing data
python track-errors.py --error-log ./data/errors.json
```

**Outputs:**
- `error-stats.json` - Complete error statistics
- `error-stats.csv` - Summary statistics
- `daily-errors.csv` - Daily error counts
- `errors-detail.csv` - Detailed error list with resolution times
- Terminal summary with trend analysis

### 3. dashboard.py

Generates comprehensive dashboards with visualizations.

**What it shows:**
- Key Performance Indicators (KPIs) with target comparisons
- Triage accuracy gauge
- High-confidence issue rate
- PR merge rate
- Time saved metrics
- Error resolution statistics
- Plugin usage charts
- Error severity distribution
- Trend analysis

**Usage:**

```bash
# Terminal dashboard
python dashboard.py --data-dir ./metrics-output --format terminal

# HTML report
python dashboard.py --data-dir ./metrics-output --format html --output report.html

# Both formats
python dashboard.py --data-dir ./metrics-output --format both

# Test with simulated data
python dashboard.py --simulate --format both
```

**Outputs:**
- Terminal: Colored, formatted dashboard with progress bars
- HTML: Interactive report with SVG gauges and charts

## Setup

### Installation

1. Install Python 3.10 or higher

2. Install dependencies (minimal - mostly stdlib):

```bash
pip install -r requirements.txt
```

3. Make scripts executable (optional):

```bash
chmod +x track-usage.py track-errors.py dashboard.py
```

### Directory Structure

```
scripts/metrics/
├── track-usage.py      # Usage tracking script
├── track-errors.py     # Error tracking script
├── dashboard.py        # Dashboard generator
├── requirements.txt    # Python dependencies
└── README.md          # This file

metrics-output/         # Default output directory (created automatically)
├── usage-stats.json
├── usage-stats.csv
├── daily-usage.csv
├── error-stats.json
├── error-stats.csv
├── daily-errors.csv
├── errors-detail.csv
└── dashboard.html
```

## Quick Start

### 1. Generate Sample Data

Test the system with simulated data:

```bash
# Generate usage data
python track-usage.py --simulate --days 30

# Generate error data
python track-errors.py --simulate --days 30

# View dashboard
python dashboard.py --simulate
```

### 2. Use with Real Data

Once you have real log files:

```bash
# Track usage from Claude logs
python track-usage.py --log-file ~/.claude/usage.log --output-dir ./metrics-output

# Track errors from error reporter
python track-errors.py --error-log ./data/error-reports.json --output-dir ./metrics-output

# Generate dashboard from collected data
python dashboard.py --data-dir ./metrics-output --format both --output report.html
```

### 3. Regular Monitoring

Set up a cron job or scheduled task to run daily:

```bash
# Create a monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
cd /path/to/xmas-challenge/scripts/metrics

# Collect metrics
python track-usage.py --log-file ~/.claude/usage.log
python track-errors.py --error-log ../../data/error-reports.json

# Generate dashboard
python dashboard.py --format html --output ../../docs/metrics-dashboard.html

echo "Metrics updated: $(date)"
EOF

chmod +x monitor.sh

# Run daily at 6 AM
# crontab -e
# 0 6 * * * /path/to/monitor.sh >> /var/log/metrics.log 2>&1
```

## Interpreting Results

### Triage Accuracy

- **80%+**: Excellent - System is reliably triaging issues
- **60-79%**: Good - Some room for improvement
- **<60%**: Needs attention - Review triage logic

### High-Confidence Rate

- **50%+**: Target met - System is confident in many issues
- **30-49%**: Acceptable - System is being cautious
- **<30%**: Low confidence - May need more training data

### PR Merge Rate

- **70%+**: Excellent - Automated fixes are high quality
- **50-69%**: Good - Most fixes are acceptable
- **<50%**: Review needed - Fixes may need improvement

### Time Saved

Calculate based on:
- Average manual triage: 15 minutes/issue
- Average fix time: 30 minutes/issue
- Review time saved: 10 minutes/PR

**Example:**
- 50 issues triaged automatically = 12.5 hours saved
- 20 fixes applied automatically = 10 hours saved
- **Total: 22.5 hours/month**

### Error Trends

- **Decreasing**: Good - System is learning and improving
- **Stable**: Acceptable - Maintaining error levels
- **Increasing**: Attention needed - Investigate causes

## Metrics Data Format

### Usage Log Format

The usage tracker expects log entries containing:

```
2024-12-15T14:30:00 plugin:component-developer@keboola-claude-kit invoked
2024-12-15T14:31:00 skill: "review" executed
2024-12-15T14:32:00 /review command completed
2024-12-15T14:35:00 error-reporter: new error reported
```

### Error Log Format

Expected JSON format:

```json
{
  "errors": [
    {
      "id": "error-1",
      "type": "TypeError",
      "severity": "high",
      "category": "validation",
      "status": "resolved",
      "reported_at": "2024-12-15T10:00:00Z",
      "resolved_at": "2024-12-15T12:30:00Z",
      "message": "Error description"
    }
  ]
}
```

Or a simple array:

```json
[
  {
    "id": "error-1",
    "type": "TypeError",
    ...
  }
]
```

### Triage Stats Format

Optional triage statistics file (`triage-stats.json`):

```json
{
  "total_issues": 120,
  "triaged_issues": 95,
  "high_confidence_issues": 62,
  "triage_accuracy": 84.2,
  "avg_confidence_score": 0.73,
  "prs_created": 45,
  "prs_merged": 34,
  "pr_merge_rate": 75.6,
  "time_saved_hours": 18.5
}
```

## Advanced Usage

### Custom Output Directory

```bash
python track-usage.py --simulate --output-dir ./custom-output
python dashboard.py --data-dir ./custom-output
```

### Specific Time Periods

```bash
# Simulate different periods
python track-usage.py --simulate --days 7   # Weekly
python track-usage.py --simulate --days 90  # Quarterly
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/metrics.yml
name: Generate Metrics

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r scripts/metrics/requirements.txt
      - name: Generate metrics
        run: |
          cd scripts/metrics
          python track-usage.py --simulate
          python track-errors.py --simulate
          python dashboard.py --format html
      - name: Upload dashboard
        uses: actions/upload-artifact@v3
        with:
          name: metrics-dashboard
          path: scripts/metrics/metrics-output/dashboard.html
```

## Troubleshooting

### No data found

- Check that log files exist and have correct paths
- Use `--simulate` to test with sample data
- Verify file permissions

### Import errors

- Ensure Python 3.10+ is installed: `python --version`
- Install requirements: `pip install -r requirements.txt`
- Check that scripts are in the correct directory

### Incorrect metrics

- Verify log file format matches expected format
- Check date/timestamp formats in logs
- Review parsed data in JSON outputs

## Contributing

To add new metrics:

1. Add tracking logic to appropriate script
2. Update `calculate_metrics()` method
3. Add visualization to dashboard
4. Update this README

## License

Part of the Self-Healing Knowledge Base Challenge

## Support

For issues or questions:
- Check existing error reports
- Review the main README.md
- Submit an issue with the error-reporter plugin
