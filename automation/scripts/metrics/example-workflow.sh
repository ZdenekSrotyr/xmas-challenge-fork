#!/bin/bash

# Example workflow for metrics tracking system
# This demonstrates how to use all three scripts together

set -e

echo "=========================================="
echo "Metrics Tracking System - Example Workflow"
echo "=========================================="
echo ""

# Set output directory
OUTPUT_DIR="./example-output"
mkdir -p "$OUTPUT_DIR"

echo "Step 1: Tracking usage statistics..."
echo "------------------------------------"
python3 track-usage.py --simulate --days 30 --output-dir "$OUTPUT_DIR"
echo ""

echo "Step 2: Tracking error statistics..."
echo "------------------------------------"
python3 track-errors.py --simulate --days 30 --errors-per-day 5 --output-dir "$OUTPUT_DIR"
echo ""

echo "Step 3: Generating dashboard..."
echo "------------------------------------"
echo ""
echo "Terminal Dashboard:"
echo "===================="
python3 dashboard.py --data-dir "$OUTPUT_DIR" --format terminal
echo ""

echo "Generating HTML report..."
python3 dashboard.py --data-dir "$OUTPUT_DIR" --format html --output report.html
echo ""

echo "=========================================="
echo "Workflow Complete!"
echo "=========================================="
echo ""
echo "Generated files in $OUTPUT_DIR:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "View the HTML report:"
echo "  open $OUTPUT_DIR/report.html"
echo ""
echo "Or on Linux:"
echo "  xdg-open $OUTPUT_DIR/report.html"
echo ""
