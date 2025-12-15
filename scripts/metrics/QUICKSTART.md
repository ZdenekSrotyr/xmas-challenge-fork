# Metrics System Quick Start Guide

## Installation

```bash
cd scripts/metrics
pip install -r requirements.txt  # No external dependencies needed!
```

## Quick Test (5 minutes)

Run the example workflow to see everything in action:

```bash
./example-workflow.sh
```

This will:
1. Generate 30 days of simulated usage data
2. Generate 30 days of simulated error data
3. Create both terminal and HTML dashboards
4. Save all outputs to `example-output/`

## Daily Usage

### Option 1: Use the Monitor Script

Customize `monitor.sh` for your environment:

```bash
# Edit paths in monitor.sh
nano monitor.sh

# Run it
./monitor.sh
```

### Option 2: Run Scripts Individually

```bash
# 1. Track usage
python3 track-usage.py --log-file ~/.claude/usage.log

# 2. Track errors
python3 track-errors.py --error-log ./data/error-reports.json

# 3. View dashboard
python3 dashboard.py --format terminal

# 4. Generate HTML report
python3 dashboard.py --format html
```

## Scheduled Monitoring

Add to crontab for daily updates:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 6 AM)
0 6 * * * /path/to/xmas-challenge/scripts/metrics/monitor.sh >> /var/log/metrics.log 2>&1
```

## Key Files

| File | Purpose |
|------|---------|
| `track-usage.py` | Track plugin/skill usage |
| `track-errors.py` | Track and analyze errors |
| `dashboard.py` | Generate dashboards |
| `monitor.sh` | Automated monitoring script |
| `example-workflow.sh` | Full demo with simulated data |

## Common Commands

### Test with Simulated Data

```bash
# Quick 7-day test
python3 track-usage.py --simulate --days 7
python3 track-errors.py --simulate --days 7
python3 dashboard.py --simulate

# Full 30-day test
./example-workflow.sh
```

### Use with Real Data

```bash
# Production monitoring
python3 track-usage.py --log-file ~/.claude/usage.log --output-dir ./metrics-output
python3 track-errors.py --error-log ./data/errors.json --output-dir ./metrics-output
python3 dashboard.py --data-dir ./metrics-output --format both
```

### View Results

```bash
# Terminal dashboard
python3 dashboard.py --format terminal

# HTML report
python3 dashboard.py --format html
open metrics-output/dashboard.html  # macOS
xdg-open metrics-output/dashboard.html  # Linux
```

## Key Metrics Explained

### Triage Accuracy (Target: 80%+)
Percentage of issues correctly triaged by the system

### High-Confidence Issues (Target: 50%+)
Percentage of issues where the system has high confidence

### PR Merge Rate (Target: 70%+)
Success rate of automated pull requests being merged

### Time Saved (Target: 15+ hours/month)
Developer time saved through automation

### Error Trend
Whether errors are increasing, decreasing, or stable

## Output Files

All files saved to `metrics-output/` (or custom directory):

- `usage-stats.json` - Complete usage statistics
- `usage-stats.csv` - Usage summary
- `daily-usage.csv` - Daily usage counts
- `error-stats.json` - Complete error statistics
- `error-stats.csv` - Error summary
- `daily-errors.csv` - Daily error counts
- `errors-detail.csv` - Detailed error list
- `dashboard.html` - Interactive HTML dashboard

## Troubleshooting

### "No data found"
- Use `--simulate` flag to test with sample data
- Check that log file paths are correct
- Verify file permissions

### "Command not found"
- Ensure scripts are executable: `chmod +x *.sh *.py`
- Use `python3` instead of `python`

### Import errors
- Verify Python 3.10+: `python3 --version`
- All scripts use only stdlib - no pip install needed!

## Integration Examples

### GitHub Actions

```yaml
- name: Generate Metrics
  run: |
    cd scripts/metrics
    python3 track-usage.py --simulate
    python3 track-errors.py --simulate
    python3 dashboard.py --format html
```

### GitLab CI

```yaml
metrics:
  script:
    - cd scripts/metrics
    - ./monitor.sh
  artifacts:
    paths:
      - scripts/metrics/metrics-output/
```

## Next Steps

1. Run `./example-workflow.sh` to test
2. Customize `monitor.sh` for your environment
3. Set up scheduled runs (cron/CI)
4. Review dashboards regularly
5. Adjust targets based on your needs

For full documentation, see [README.md](README.md)
