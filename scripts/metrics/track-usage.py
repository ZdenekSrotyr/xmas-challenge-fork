#!/usr/bin/env python3
"""
Track usage statistics for the self-healing knowledge base.

This script monitors:
- Plugin usage stats (how often each plugin is invoked)
- Skill triggers (which skills are being used)
- Error reporter usage (how often errors are reported)
- Exports data to JSON and CSV formats

Usage:
    python track-usage.py --log-file path/to/claude-usage.log --output-dir ./output
    python track-usage.py --simulate  # Generate sample data for testing
"""

import argparse
import json
import csv
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


class UsageTracker:
    """Track and analyze usage statistics for the knowledge base."""

    def __init__(self, output_dir: str = "./metrics-output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "plugins": defaultdict(int),
            "skills": defaultdict(int),
            "error_reports": 0,
            "slash_commands": defaultdict(int),
            "timestamps": [],
            "daily_usage": defaultdict(int),
            "hourly_usage": defaultdict(int),
        }

    def parse_log_file(self, log_file: str) -> None:
        """Parse Claude usage log file for statistics."""
        print(f"Parsing log file: {log_file}")

        if not os.path.exists(log_file):
            print(f"Warning: Log file not found: {log_file}")
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                self._parse_line(line)

        print(f"Parsed {len(self.stats['timestamps'])} usage events")

    def _parse_line(self, line: str) -> None:
        """Parse a single log line for usage information."""
        # Look for plugin invocations: plugin:name@package
        plugin_match = re.search(r'plugin:(\w+)@([\w-]+)', line)
        if plugin_match:
            plugin_name = plugin_match.group(1)
            self.stats["plugins"][plugin_name] += 1
            self._record_timestamp(line)

        # Look for skill invocations: skill: "name"
        skill_match = re.search(r'skill:\s*"(\w+)"', line)
        if skill_match:
            skill_name = skill_match.group(1)
            self.stats["skills"][skill_name] += 1
            self._record_timestamp(line)

        # Look for slash commands: /command-name
        command_match = re.search(r'/(\w+(?:-\w+)*)', line)
        if command_match:
            command = command_match.group(1)
            self.stats["slash_commands"][command] += 1
            self._record_timestamp(line)

        # Look for error reporter usage
        if "error-reporter" in line.lower() or "report-error" in line.lower():
            self.stats["error_reports"] += 1
            self._record_timestamp(line)

    def _record_timestamp(self, line: str) -> None:
        """Extract and record timestamp from log line."""
        # Try to extract ISO timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1).replace('T', ' ')
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                self.stats["timestamps"].append(dt)

                # Record daily usage
                date_key = dt.strftime('%Y-%m-%d')
                self.stats["daily_usage"][date_key] += 1

                # Record hourly usage
                hour_key = dt.strftime('%H:00')
                self.stats["hourly_usage"][hour_key] += 1
            except ValueError:
                pass

    def simulate_data(self, days: int = 30) -> None:
        """Generate simulated usage data for testing."""
        print(f"Generating simulated data for {days} days")

        plugins = ["component-developer", "error-reporter", "knowledge-base", "triage"]
        skills = ["review", "fix", "analyze", "debug"]
        commands = ["review", "fix", "triage", "report-error"]

        import random

        start_date = datetime.now() - timedelta(days=days)

        for day in range(days):
            # More usage on weekdays, less on weekends
            current_date = start_date + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5
            daily_events = random.randint(5, 15) if not is_weekend else random.randint(1, 5)

            for _ in range(daily_events):
                # Random hour (work hours more likely)
                hour = random.choices(
                    range(24),
                    weights=[1]*8 + [5]*8 + [2]*8  # 8am-4pm more likely
                )[0]

                event_time = current_date.replace(hour=hour, minute=random.randint(0, 59))

                # Simulate different events
                event_type = random.choices(
                    ["plugin", "skill", "command", "error"],
                    weights=[40, 30, 25, 5]
                )[0]

                if event_type == "plugin":
                    plugin = random.choice(plugins)
                    self.stats["plugins"][plugin] += 1
                elif event_type == "skill":
                    skill = random.choice(skills)
                    self.stats["skills"][skill] += 1
                elif event_type == "command":
                    command = random.choice(commands)
                    self.stats["slash_commands"][command] += 1
                else:
                    self.stats["error_reports"] += 1

                self.stats["timestamps"].append(event_time)

                # Record daily/hourly
                date_key = event_time.strftime('%Y-%m-%d')
                self.stats["daily_usage"][date_key] += 1
                hour_key = event_time.strftime('%H:00')
                self.stats["hourly_usage"][hour_key] += 1

        print(f"Generated {len(self.stats['timestamps'])} simulated events")

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate summary metrics from collected statistics."""
        total_events = len(self.stats["timestamps"])

        metrics = {
            "total_events": total_events,
            "total_plugins": sum(self.stats["plugins"].values()),
            "total_skills": sum(self.stats["skills"].values()),
            "total_commands": sum(self.stats["slash_commands"].values()),
            "error_reports": self.stats["error_reports"],
            "unique_plugins": len(self.stats["plugins"]),
            "unique_skills": len(self.stats["skills"]),
            "unique_commands": len(self.stats["slash_commands"]),
        }

        # Calculate date range
        if self.stats["timestamps"]:
            timestamps = sorted(self.stats["timestamps"])
            metrics["first_event"] = timestamps[0].isoformat()
            metrics["last_event"] = timestamps[-1].isoformat()
            metrics["date_range_days"] = (timestamps[-1] - timestamps[0]).days + 1
            metrics["avg_events_per_day"] = total_events / max(metrics["date_range_days"], 1)
        else:
            metrics["first_event"] = None
            metrics["last_event"] = None
            metrics["date_range_days"] = 0
            metrics["avg_events_per_day"] = 0

        # Most popular items
        if self.stats["plugins"]:
            metrics["most_used_plugin"] = max(self.stats["plugins"].items(), key=lambda x: x[1])
        if self.stats["skills"]:
            metrics["most_used_skill"] = max(self.stats["skills"].items(), key=lambda x: x[1])
        if self.stats["slash_commands"]:
            metrics["most_used_command"] = max(self.stats["slash_commands"].items(), key=lambda x: x[1])

        return metrics

    def export_json(self, filename: str = "usage-stats.json") -> str:
        """Export statistics to JSON format."""
        output_path = self.output_dir / filename

        # Convert defaultdicts to regular dicts for JSON serialization
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "metrics": self.calculate_metrics(),
            "plugins": dict(self.stats["plugins"]),
            "skills": dict(self.stats["skills"]),
            "slash_commands": dict(self.stats["slash_commands"]),
            "daily_usage": dict(self.stats["daily_usage"]),
            "hourly_usage": dict(self.stats["hourly_usage"]),
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        print(f"Exported JSON to: {output_path}")
        return str(output_path)

    def export_csv(self, filename: str = "usage-stats.csv") -> str:
        """Export statistics to CSV format."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write plugins
            writer.writerow(["Category", "Name", "Count"])
            for plugin, count in sorted(self.stats["plugins"].items(), key=lambda x: -x[1]):
                writer.writerow(["Plugin", plugin, count])

            # Write skills
            for skill, count in sorted(self.stats["skills"].items(), key=lambda x: -x[1]):
                writer.writerow(["Skill", skill, count])

            # Write commands
            for command, count in sorted(self.stats["slash_commands"].items(), key=lambda x: -x[1]):
                writer.writerow(["Command", command, count])

            # Write error reports
            writer.writerow(["Error Reports", "Total", self.stats["error_reports"]])

        print(f"Exported CSV to: {output_path}")
        return str(output_path)

    def export_daily_csv(self, filename: str = "daily-usage.csv") -> str:
        """Export daily usage statistics to CSV."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Events"])

            for date, count in sorted(self.stats["daily_usage"].items()):
                writer.writerow([date, count])

        print(f"Exported daily usage CSV to: {output_path}")
        return str(output_path)

    def print_summary(self) -> None:
        """Print a human-readable summary of usage statistics."""
        metrics = self.calculate_metrics()

        print("\n" + "=" * 60)
        print("USAGE STATISTICS SUMMARY")
        print("=" * 60)

        print(f"\nTotal Events: {metrics['total_events']}")
        if metrics['first_event']:
            print(f"Date Range: {metrics['first_event'][:10]} to {metrics['last_event'][:10]}")
            print(f"Duration: {metrics['date_range_days']} days")
            print(f"Avg Events/Day: {metrics['avg_events_per_day']:.1f}")

        print(f"\n--- Plugins ---")
        print(f"Total Plugin Invocations: {metrics['total_plugins']}")
        print(f"Unique Plugins: {metrics['unique_plugins']}")
        if self.stats["plugins"]:
            print("\nPlugin Usage:")
            for plugin, count in sorted(self.stats["plugins"].items(), key=lambda x: -x[1]):
                percentage = (count / metrics['total_plugins'] * 100) if metrics['total_plugins'] > 0 else 0
                print(f"  {plugin:30} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- Skills ---")
        print(f"Total Skill Triggers: {metrics['total_skills']}")
        print(f"Unique Skills: {metrics['unique_skills']}")
        if self.stats["skills"]:
            print("\nSkill Usage:")
            for skill, count in sorted(self.stats["skills"].items(), key=lambda x: -x[1]):
                percentage = (count / metrics['total_skills'] * 100) if metrics['total_skills'] > 0 else 0
                print(f"  {skill:30} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- Slash Commands ---")
        print(f"Total Command Invocations: {metrics['total_commands']}")
        print(f"Unique Commands: {metrics['unique_commands']}")
        if self.stats["slash_commands"]:
            print("\nCommand Usage:")
            for command, count in sorted(self.stats["slash_commands"].items(), key=lambda x: -x[1]):
                percentage = (count / metrics['total_commands'] * 100) if metrics['total_commands'] > 0 else 0
                print(f"  {command:30} {count:4} ({percentage:5.1f}%)")

        print(f"\n--- Error Reports ---")
        print(f"Total Error Reports: {metrics['error_reports']}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Track usage statistics for the self-healing knowledge base"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to Claude usage log file to parse"
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
        "--json-output",
        type=str,
        default="usage-stats.json",
        help="JSON output filename (default: usage-stats.json)"
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        default="usage-stats.csv",
        help="CSV output filename (default: usage-stats.csv)"
    )

    args = parser.parse_args()

    tracker = UsageTracker(output_dir=args.output_dir)

    if args.simulate:
        tracker.simulate_data(days=args.days)
    elif args.log_file:
        tracker.parse_log_file(args.log_file)
    else:
        print("Error: Must specify either --log-file or --simulate")
        parser.print_help()
        return 1

    # Print summary
    tracker.print_summary()

    # Export data
    print("\nExporting data...")
    tracker.export_json(args.json_output)
    tracker.export_csv(args.csv_output)
    tracker.export_daily_csv("daily-usage.csv")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
