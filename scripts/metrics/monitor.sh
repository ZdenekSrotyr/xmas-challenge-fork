#!/bin/bash

# Monitoring script for self-healing knowledge base metrics
# Customize this script for your environment and run regularly (e.g., via cron)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/metrics-output"
LOG_DIR="${HOME}/.claude"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Data sources (customize these paths for your environment)
USAGE_LOG="${LOG_DIR}/usage.log"
ERROR_LOG="${PROJECT_ROOT}/data/error-reports.json"
DASHBOARD_OUTPUT="${PROJECT_ROOT}/docs/metrics-dashboard.html"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Metrics Collection - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# Track usage statistics
echo "Collecting usage statistics..."
if [ -f "$USAGE_LOG" ]; then
    python3 "${SCRIPT_DIR}/track-usage.py" \
        --log-file "$USAGE_LOG" \
        --output-dir "$OUTPUT_DIR"
else
    echo "Warning: Usage log not found at $USAGE_LOG"
    echo "Using simulated data for testing..."
    python3 "${SCRIPT_DIR}/track-usage.py" \
        --simulate \
        --days 30 \
        --output-dir "$OUTPUT_DIR"
fi
echo ""

# Track error statistics
echo "Collecting error statistics..."
if [ -f "$ERROR_LOG" ]; then
    python3 "${SCRIPT_DIR}/track-errors.py" \
        --error-log "$ERROR_LOG" \
        --output-dir "$OUTPUT_DIR"
else
    echo "Warning: Error log not found at $ERROR_LOG"
    echo "Using simulated data for testing..."
    python3 "${SCRIPT_DIR}/track-errors.py" \
        --simulate \
        --days 30 \
        --output-dir "$OUTPUT_DIR"
fi
echo ""

# Generate dashboard
echo "Generating dashboard..."
python3 "${SCRIPT_DIR}/dashboard.py" \
    --data-dir "$OUTPUT_DIR" \
    --format both \
    --output "dashboard.html"
echo ""

# Copy dashboard to docs if directory exists
if [ -d "${PROJECT_ROOT}/docs" ]; then
    cp "${OUTPUT_DIR}/dashboard.html" "$DASHBOARD_OUTPUT"
    echo "Dashboard copied to: $DASHBOARD_OUTPUT"
fi

echo "=========================================="
echo "Metrics collection complete!"
echo "=========================================="
echo ""
echo "Files generated in: $OUTPUT_DIR"
echo ""

# Optional: Archive old metrics
ARCHIVE_DIR="${OUTPUT_DIR}/archive"
if [ -d "$ARCHIVE_DIR" ]; then
    TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
    mkdir -p "${ARCHIVE_DIR}/${TIMESTAMP}"
    cp "${OUTPUT_DIR}"/*.json "${ARCHIVE_DIR}/${TIMESTAMP}/" 2>/dev/null || true
    echo "Metrics archived to: ${ARCHIVE_DIR}/${TIMESTAMP}"
fi

# Optional: Send notification (customize as needed)
# Example: Send email, post to Slack, etc.
# if [ -f "${OUTPUT_DIR}/dashboard.html" ]; then
#     echo "Dashboard available at: file://${OUTPUT_DIR}/dashboard.html"
# fi

exit 0
