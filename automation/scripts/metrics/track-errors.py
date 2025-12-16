#!/usr/bin/env python3
"""
Track error statistics for the self-healing knowledge base.

This script monitors:
- Reported errors over time
- Error type categorization
- Resolution time tracking
- Error trends and patterns

Usage:
    python track-errors.py --error-log path/to/errors.json --output-dir ./output
    python track-errors.py --simulate  # Generate sample data for testing
"""

import argparse
import json
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional


class ErrorTracker:
    """Track and analyze error statistics for the knowledge base."""

    def __init__(self, output_dir: str = "./metrics-output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.errors = []
        self.stats = {
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int),
            "by_status": defaultdict(int),
            "by_category": defaultdict(int),
            "daily_errors": defaultdict(int),
            "resolution_times": [],
        }

    def load_error_log(self, log_file: str) -> None:
        """Load errors from JSON log file."""
        print(f"Loading error log: {log_file}")

        if not os.path.exists(log_file):
            print(f"Warning: Error log not found: {log_file}")
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            self.errors = data
        elif isinstance(data, dict) and "errors" in data:
            self.errors = data["errors"]
        else:
            print("Warning: Unexpected error log format")
            return

        print(f"Loaded {len(self.errors)} errors")
        self._process_errors()

    def _process_errors(self) -> None:
        """Process loaded errors and calculate statistics."""
        for error in self.errors:
            # Count by type
            error_type = error.get("type", "unknown")
            self.stats["by_type"][error_type] += 1

            # Count by severity
            severity = error.get("severity", "unknown")
            self.stats["by_severity"][severity] += 1

            # Count by status
            status = error.get("status", "open")
            self.stats["by_status"][status] += 1

            # Count by category
            category = error.get("category", "uncategorized")
            self.stats["by_category"][category] += 1

            # Daily errors
            timestamp = error.get("timestamp", error.get("reported_at"))
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = dt.strftime('%Y-%m-%d')
                    self.stats["daily_errors"][date_key] += 1
                except (ValueError, AttributeError):
                    pass

            # Resolution time
            if error.get("status") == "resolved":
                resolved_at = error.get("resolved_at")
                reported_at = error.get("reported_at", error.get("timestamp"))

                if resolved_at and reported_at:
                    try:
                        resolved_dt = datetime.fromisoformat(resolved_at.replace('Z', '+00:00'))
                        reported_dt = datetime.fromisoformat(reported_at.replace('Z', '+00:00'))
                        resolution_time = (resolved_dt - reported_dt).total_seconds() / 3600  # hours
                        self.stats["resolution_times"].append(resolution_time)
                    except (ValueError, AttributeError):
                        pass

    def simulate_data(self, days: int = 30, errors_per_day: int = 5) -> None:
        """Generate simulated error data for testing."""
        print(f"Generating simulated error data for {days} days")

        import random

        error_types = [
            "TypeError", "ValueError", "AttributeError", "KeyError",
            "ImportError", "FileNotFoundError", "ConnectionError",
            "TimeoutError", "ConfigurationError", "ValidationError"
        ]

        severities = ["critical", "high", "medium", "low"]
        severity_weights = [5, 15, 40, 40]  # Most errors are low/medium

        categories = [
            "configuration", "validation", "api", "database",
            "file-handling", "network", "auth", "data-processing"
        ]

        start_date = datetime.now() - timedelta(days=days)

        for day in range(days):
            current_date = start_date + timedelta(days=day)

            # Fewer errors on weekends
            is_weekend = current_date.weekday() >= 5
            daily_count = random.randint(1, errors_per_day // 2) if is_weekend else random.randint(2, errors_per_day)

            for _ in range(daily_count):
                # Random time during the day
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                error_time = current_date.replace(hour=hour, minute=minute)

                severity = random.choices(severities, weights=severity_weights)[0]
                error_type = random.choice(error_types)
                category = random.choice(categories)

                # Most errors get resolved
                status = random.choices(["resolved", "open", "investigating"], weights=[70, 20, 10])[0]

                error = {
                    "id": f"error-{len(self.errors) + 1}",
                    "type": error_type,
                    "severity": severity,
                    "category": category,
                    "status": status,
                    "reported_at": error_time.isoformat(),
                    "message": f"Simulated {error_type} in {category}",
                }

                # Add resolution time for resolved errors
                if status == "resolved":
                    # Resolution time depends on severity
                    if severity == "critical":
                        hours = random.uniform(0.5, 4)
                    elif severity == "high":
                        hours = random.uniform(2, 12)
                    elif severity == "medium":
                        hours = random.uniform(4, 48)
                    else:
                        hours = random.uniform(12, 168)  # up to a week

                    resolved_time = error_time + timedelta(hours=hours)
                    error["resolved_at"] = resolved_time.isoformat()

                self.errors.append(error)

        print(f"Generated {len(self.errors)} simulated errors")
        self._process_errors()

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate summary metrics from collected error data."""
        metrics = {
            "total_errors": len(self.errors),
            "by_type": dict(self.stats["by_type"]),
            "by_severity": dict(self.stats["by_severity"]),
            "by_status": dict(self.stats["by_status"]),
            "by_category": dict(self.stats["by_category"]),
        }

        # Resolution statistics
        if self.stats["resolution_times"]:
            resolution_times = self.stats["resolution_times"]
            metrics["avg_resolution_time_hours"] = sum(resolution_times) / len(resolution_times)
            metrics["median_resolution_time_hours"] = sorted(resolution_times)[len(resolution_times) // 2]
            metrics["min_resolution_time_hours"] = min(resolution_times)
            metrics["max_resolution_time_hours"] = max(resolution_times)
            metrics["total_resolved"] = len(resolution_times)
        else:
            metrics["avg_resolution_time_hours"] = 0
            metrics["median_resolution_time_hours"] = 0
            metrics["min_resolution_time_hours"] = 0
            metrics["max_resolution_time_hours"] = 0
            metrics["total_resolved"] = 0

        # Resolution rate
        if len(self.errors) > 0:
            metrics["resolution_rate"] = (self.stats["by_status"]["resolved"] / len(self.errors)) * 100
        else:
            metrics["resolution_rate"] = 0

        # Date range
        if self.errors:
            timestamps = []
            for error in self.errors:
                timestamp = error.get("timestamp", error.get("reported_at"))
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamps.append(dt)
                    except (ValueError, AttributeError):
                        pass

            if timestamps:
                timestamps.sort()
                metrics["first_error"] = timestamps[0].isoformat()
                metrics["last_error"] = timestamps[-1].isoformat()
                metrics["date_range_days"] = (timestamps[-1] - timestamps[0]).days + 1
                metrics["avg_errors_per_day"] = len(self.errors) / max(metrics["date_range_days"], 1)
            else:
                metrics["first_error"] = None
                metrics["last_error"] = None
                metrics["date_range_days"] = 0
                metrics["avg_errors_per_day"] = 0
        else:
            metrics["first_error"] = None
            metrics["last_error"] = None
            metrics["date_range_days"] = 0
            metrics["avg_errors_per_day"] = 0

        # Trend analysis - compare recent vs older errors
        if len(self.errors) >= 10 and self.stats["daily_errors"]:
            dates = sorted(self.stats["daily_errors"].keys())
            mid_point = len(dates) // 2

            recent_dates = dates[mid_point:]
            older_dates = dates[:mid_point]

            recent_count = sum(self.stats["daily_errors"][d] for d in recent_dates)
            older_count = sum(self.stats["daily_errors"][d] for d in older_dates)

            recent_avg = recent_count / len(recent_dates) if recent_dates else 0
            older_avg = older_count / len(older_dates) if older_dates else 0

            if older_avg > 0:
                trend = ((recent_avg - older_avg) / older_avg) * 100
                metrics["error_trend_percentage"] = trend
                metrics["trend_direction"] = "decreasing" if trend < -5 else "increasing" if trend > 5 else "stable"
            else:
                metrics["error_trend_percentage"] = 0
                metrics["trend_direction"] = "unknown"
        else:
            metrics["error_trend_percentage"] = 0
            metrics["trend_direction"] = "insufficient_data"

        return metrics

    def export_json(self, filename: str = "error-stats.json") -> str:
        """Export error statistics to JSON format."""
        output_path = self.output_dir / filename

        export_data = {
            "generated_at": datetime.now().isoformat(),
            "metrics": self.calculate_metrics(),
            "daily_errors": dict(self.stats["daily_errors"]),
            "errors": self.errors,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        print(f"Exported JSON to: {output_path}")
        return str(output_path)

    def export_csv(self, filename: str = "error-stats.csv") -> str:
        """Export error statistics to CSV format."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(["Category", "Subcategory", "Count"])

            # Write by type
            for error_type, count in sorted(self.stats["by_type"].items(), key=lambda x: -x[1]):
                writer.writerow(["Type", error_type, count])

            # Write by severity
            for severity, count in sorted(self.stats["by_severity"].items(), key=lambda x: -x[1]):
                writer.writerow(["Severity", severity, count])

            # Write by status
            for status, count in sorted(self.stats["by_status"].items(), key=lambda x: -x[1]):
                writer.writerow(["Status", status, count])

            # Write by category
            for category, count in sorted(self.stats["by_category"].items(), key=lambda x: -x[1]):
                writer.writerow(["Category", category, count])

        print(f"Exported CSV to: {output_path}")
        return str(output_path)

    def export_daily_csv(self, filename: str = "daily-errors.csv") -> str:
        """Export daily error counts to CSV."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Error Count"])

            for date, count in sorted(self.stats["daily_errors"].items()):
                writer.writerow([date, count])

        print(f"Exported daily errors CSV to: {output_path}")
        return str(output_path)

    def export_errors_csv(self, filename: str = "errors-detail.csv") -> str:
        """Export detailed error list to CSV."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Type", "Severity", "Category", "Status",
                "Reported At", "Resolved At", "Resolution Time (hours)", "Message"
            ])

            for error in self.errors:
                resolution_time = ""
                if error.get("status") == "resolved" and error.get("resolved_at") and error.get("reported_at"):
                    try:
                        resolved_dt = datetime.fromisoformat(error["resolved_at"].replace('Z', '+00:00'))
                        reported_dt = datetime.fromisoformat(error["reported_at"].replace('Z', '+00:00'))
                        hours = (resolved_dt - reported_dt).total_seconds() / 3600
                        resolution_time = f"{hours:.2f}"
                    except (ValueError, AttributeError):
                        pass

                writer.writerow([
                    error.get("id", ""),
                    error.get("type", ""),
                    error.get("severity", ""),
                    error.get("category", ""),
                    error.get("status", ""),
                    error.get("reported_at", ""),
                    error.get("resolved_at", ""),
                    resolution_time,
                    error.get("message", "")[:100]  # Truncate long messages
                ])

        print(f"Exported detailed errors CSV to: {output_path}")
        return str(output_path)

    def print_summary(self) -> None:
        """Print a human-readable summary of error statistics."""
        metrics = self.calculate_metrics()

        print("\n" + "=" * 60)
        print("ERROR STATISTICS SUMMARY")
        print("=" * 60)

        print(f"\nTotal Errors: {metrics['total_errors']}")
        if metrics['first_error']:
            print(f"Date Range: {metrics['first_error'][:10]} to {metrics['last_error'][:10]}")
            print(f"Duration: {metrics['date_range_days']} days")
            print(f"Avg Errors/Day: {metrics['avg_errors_per_day']:.1f}")

        print(f"\n--- Error Trend ---")
        print(f"Trend: {metrics['trend_direction']}")
        if metrics['error_trend_percentage'] != 0:
            print(f"Change: {metrics['error_trend_percentage']:+.1f}% (recent vs older period)")

        print(f"\n--- By Severity ---")
        severity_order = ["critical", "high", "medium", "low"]
        for severity in severity_order:
            count = metrics['by_severity'].get(severity, 0)
            percentage = (count / metrics['total_errors'] * 100) if metrics['total_errors'] > 0 else 0
            print(f"  {severity.capitalize():12} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- By Status ---")
        for status, count in sorted(metrics['by_status'].items(), key=lambda x: -x[1]):
            percentage = (count / metrics['total_errors'] * 100) if metrics['total_errors'] > 0 else 0
            print(f"  {status.capitalize():12} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- Resolution Metrics ---")
        print(f"Resolution Rate: {metrics['resolution_rate']:.1f}%")
        print(f"Total Resolved: {metrics['total_resolved']}")
        if metrics['total_resolved'] > 0:
            print(f"Avg Resolution Time: {metrics['avg_resolution_time_hours']:.1f} hours")
            print(f"Median Resolution Time: {metrics['median_resolution_time_hours']:.1f} hours")
            print(f"Min Resolution Time: {metrics['min_resolution_time_hours']:.1f} hours")
            print(f"Max Resolution Time: {metrics['max_resolution_time_hours']:.1f} hours")

        print(f"\n--- By Type (Top 10) ---")
        sorted_types = sorted(metrics['by_type'].items(), key=lambda x: -x[1])[:10]
        for error_type, count in sorted_types:
            percentage = (count / metrics['total_errors'] * 100) if metrics['total_errors'] > 0 else 0
            print(f"  {error_type:30} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- By Category ---")
        for category, count in sorted(metrics['by_category'].items(), key=lambda x: -x[1]):
            percentage = (count / metrics['total_errors'] * 100) if metrics['total_errors'] > 0 else 0
            print(f"  {category:30} {count:4} ({percentage:5.1f}%)")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Track error statistics for the self-healing knowledge base"
    )
    parser.add_argument(
        "--error-log",
        type=str,
        help="Path to error log JSON file to parse"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./metrics-output",
        help="Directory to save output files (default: ./metrics-output)"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Generate simulated data for testing"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to simulate (default: 30)"
    )
    parser.add_argument(
        "--errors-per-day",
        type=int,
        default=5,
        help="Average errors per day for simulation (default: 5)"
    )

    args = parser.parse_args()

    tracker = ErrorTracker(output_dir=args.output_dir)

    if args.simulate:
        tracker.simulate_data(days=args.days, errors_per_day=args.errors_per_day)
    elif args.error_log:
        tracker.load_error_log(args.error_log)
    else:
        print("Error: Must specify either --error-log or --simulate")
        parser.print_help()
        return 1

    # Print summary
    tracker.print_summary()

    # Export data
    print("\nExporting data...")
    tracker.export_json()
    tracker.export_csv()
    tracker.export_daily_csv()
    tracker.export_errors_csv()

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
