#!/usr/bin/env python3
"""
Dashboard for visualizing self-healing knowledge base metrics.

This script generates:
- Terminal-based dashboard with key metrics
- HTML report with charts and visualizations
- Metrics tracking:
  * Triage accuracy (target 80%+)
  * High-confidence issues (target 50%+)
  * PR merge rate (target 70%+)
  * Time saved (target 15+ hours/month)
  * Issue reduction over time

Usage:
    python dashboard.py --data-dir ./metrics-output --format terminal
    python dashboard.py --data-dir ./metrics-output --format html --output report.html
    python dashboard.py --simulate  # Generate sample metrics and display
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import math


class MetricsDashboard:
    """Generate and display metrics dashboard for the knowledge base."""

    def __init__(self, data_dir: str = "./metrics-output"):
        self.data_dir = Path(data_dir)
        self.metrics = {}

        # Target metrics from README
        self.targets = {
            "triage_accuracy": 80.0,
            "high_confidence_rate": 50.0,
            "pr_merge_rate": 70.0,
            "time_saved_monthly": 15.0,  # hours
        }

    def load_metrics(self) -> None:
        """Load all available metrics from data directory."""
        print(f"Loading metrics from: {self.data_dir}")

        # Load usage stats
        usage_file = self.data_dir / "usage-stats.json"
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                self.metrics["usage"] = json.load(f)
            print(f"  Loaded usage stats")

        # Load error stats
        error_file = self.data_dir / "error-stats.json"
        if error_file.exists():
            with open(error_file, 'r') as f:
                self.metrics["errors"] = json.load(f)
            print(f"  Loaded error stats")

        # Load triage stats (if available)
        triage_file = self.data_dir / "triage-stats.json"
        if triage_file.exists():
            with open(triage_file, 'r') as f:
                self.metrics["triage"] = json.load(f)
            print(f"  Loaded triage stats")

    def simulate_metrics(self) -> None:
        """Generate simulated metrics for testing."""
        print("Generating simulated metrics...")

        import random

        # Simulate usage metrics
        self.metrics["usage"] = {
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "total_events": 450,
                "total_plugins": 180,
                "total_skills": 120,
                "total_commands": 140,
                "error_reports": 10,
                "date_range_days": 30,
                "avg_events_per_day": 15.0,
            },
            "plugins": {
                "component-developer": 85,
                "error-reporter": 45,
                "triage": 35,
                "knowledge-base": 15,
            },
        }

        # Simulate error metrics
        errors = []
        for i in range(50):
            severity = random.choices(["critical", "high", "medium", "low"], weights=[5, 15, 40, 40])[0]
            status = random.choices(["resolved", "open", "investigating"], weights=[75, 15, 10])[0]

            error = {
                "id": f"error-{i+1}",
                "severity": severity,
                "status": status,
            }

            if status == "resolved":
                if severity == "critical":
                    hours = random.uniform(0.5, 4)
                elif severity == "high":
                    hours = random.uniform(2, 12)
                else:
                    hours = random.uniform(4, 48)
                error["resolution_time"] = hours

            errors.append(error)

        self.metrics["errors"] = {
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "total_errors": 50,
                "total_resolved": 38,
                "resolution_rate": 76.0,
                "avg_resolution_time_hours": 18.5,
                "date_range_days": 30,
                "avg_errors_per_day": 1.67,
                "by_severity": {
                    "critical": 3,
                    "high": 8,
                    "medium": 20,
                    "low": 19,
                },
                "trend_direction": "decreasing",
                "error_trend_percentage": -15.5,
            },
            "errors": errors,
        }

        # Simulate triage metrics
        self.metrics["triage"] = {
            "generated_at": datetime.now().isoformat(),
            "total_issues": 120,
            "triaged_issues": 95,
            "high_confidence_issues": 62,
            "triage_accuracy": 84.2,
            "avg_confidence_score": 0.73,
            "prs_created": 45,
            "prs_merged": 34,
            "pr_merge_rate": 75.6,
            "time_saved_hours": 18.5,
        }

        print("Simulated metrics generated")

    def calculate_kpis(self) -> Dict[str, Any]:
        """Calculate key performance indicators from loaded metrics."""
        kpis = {
            "triage_accuracy": 0.0,
            "high_confidence_rate": 0.0,
            "pr_merge_rate": 0.0,
            "time_saved_monthly": 0.0,
            "error_resolution_rate": 0.0,
            "error_trend": "unknown",
            "total_events": 0,
            "total_errors": 0,
        }

        # Triage metrics
        if "triage" in self.metrics:
            triage = self.metrics["triage"]
            kpis["triage_accuracy"] = triage.get("triage_accuracy", 0.0)

            total_issues = triage.get("total_issues", 0)
            high_conf = triage.get("high_confidence_issues", 0)
            kpis["high_confidence_rate"] = (high_conf / total_issues * 100) if total_issues > 0 else 0.0

            prs_merged = triage.get("prs_merged", 0)
            prs_created = triage.get("prs_created", 0)
            kpis["pr_merge_rate"] = (prs_merged / prs_created * 100) if prs_created > 0 else 0.0

            kpis["time_saved_monthly"] = triage.get("time_saved_hours", 0.0)

        # Error metrics
        if "errors" in self.metrics:
            error_metrics = self.metrics["errors"].get("metrics", {})
            kpis["error_resolution_rate"] = error_metrics.get("resolution_rate", 0.0)
            kpis["error_trend"] = error_metrics.get("trend_direction", "unknown")
            kpis["total_errors"] = error_metrics.get("total_errors", 0)
            kpis["avg_resolution_time"] = error_metrics.get("avg_resolution_time_hours", 0.0)

        # Usage metrics
        if "usage" in self.metrics:
            usage_metrics = self.metrics["usage"].get("metrics", {})
            kpis["total_events"] = usage_metrics.get("total_events", 0)
            kpis["plugin_usage"] = usage_metrics.get("total_plugins", 0)

        return kpis

    def print_terminal_dashboard(self) -> None:
        """Print a terminal-based dashboard with key metrics."""
        kpis = self.calculate_kpis()

        # Terminal colors
        RESET = "\033[0m"
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        CYAN = "\033[96m"

        def status_color(value: float, target: float, higher_is_better: bool = True) -> str:
            """Return color based on target achievement."""
            if higher_is_better:
                if value >= target:
                    return GREEN
                elif value >= target * 0.8:
                    return YELLOW
                else:
                    return RED
            else:
                if value <= target:
                    return GREEN
                elif value <= target * 1.2:
                    return YELLOW
                else:
                    return RED

        def progress_bar(value: float, target: float, width: int = 40) -> str:
            """Create a simple text progress bar."""
            percentage = min(value / target, 1.0) if target > 0 else 0
            filled = int(width * percentage)
            bar = "█" * filled + "░" * (width - filled)
            return bar

        print("\n" + BOLD + CYAN + "=" * 80)
        print("SELF-HEALING KNOWLEDGE BASE DASHBOARD")
        print("=" * 80 + RESET)

        # Header info
        print(f"\n{BOLD}Generated:{RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if "usage" in self.metrics:
            date_range = self.metrics["usage"].get("metrics", {}).get("date_range_days", 0)
            print(f"{BOLD}Data Period:{RESET} Last {date_range} days")
        print()

        # Key Performance Indicators
        print(BOLD + BLUE + "KEY PERFORMANCE INDICATORS" + RESET)
        print("-" * 80)

        # Triage Accuracy
        triage_acc = kpis["triage_accuracy"]
        target = self.targets["triage_accuracy"]
        color = status_color(triage_acc, target)
        print(f"\n{BOLD}Triage Accuracy:{RESET}")
        print(f"  {color}{triage_acc:5.1f}%{RESET} (Target: {target:.0f}%+)")
        print(f"  [{progress_bar(triage_acc, target)}]")

        # High Confidence Rate
        high_conf = kpis["high_confidence_rate"]
        target = self.targets["high_confidence_rate"]
        color = status_color(high_conf, target)
        print(f"\n{BOLD}High-Confidence Issues:{RESET}")
        print(f"  {color}{high_conf:5.1f}%{RESET} (Target: {target:.0f}%+)")
        print(f"  [{progress_bar(high_conf, target)}]")

        # PR Merge Rate
        pr_merge = kpis["pr_merge_rate"]
        target = self.targets["pr_merge_rate"]
        color = status_color(pr_merge, target)
        print(f"\n{BOLD}PR Merge Rate:{RESET}")
        print(f"  {color}{pr_merge:5.1f}%{RESET} (Target: {target:.0f}%+)")
        print(f"  [{progress_bar(pr_merge, target)}]")

        # Time Saved
        time_saved = kpis["time_saved_monthly"]
        target = self.targets["time_saved_monthly"]
        color = status_color(time_saved, target)
        print(f"\n{BOLD}Time Saved (Monthly):{RESET}")
        print(f"  {color}{time_saved:5.1f} hours{RESET} (Target: {target:.0f}+ hours)")
        print(f"  [{progress_bar(time_saved, target)}]")

        # Additional Metrics
        print(f"\n{BOLD + BLUE}ADDITIONAL METRICS{RESET}")
        print("-" * 80)

        # Error Resolution
        error_res = kpis["error_resolution_rate"]
        print(f"\n{BOLD}Error Resolution Rate:{RESET} {error_res:.1f}%")

        error_trend = kpis["error_trend"]
        if error_trend == "decreasing":
            trend_color = GREEN
            trend_icon = "↓"
        elif error_trend == "increasing":
            trend_color = RED
            trend_icon = "↑"
        else:
            trend_color = YELLOW
            trend_icon = "→"
        print(f"{BOLD}Error Trend:{RESET} {trend_color}{trend_icon} {error_trend}{RESET}")

        if kpis.get("avg_resolution_time"):
            print(f"{BOLD}Avg Resolution Time:{RESET} {kpis['avg_resolution_time']:.1f} hours")

        # Usage stats
        print(f"\n{BOLD}Total Events:{RESET} {kpis['total_events']}")
        print(f"{BOLD}Plugin Usage:{RESET} {kpis['plugin_usage']} invocations")
        print(f"{BOLD}Total Errors:{RESET} {kpis['total_errors']}")

        # Plugin breakdown
        if "usage" in self.metrics and "plugins" in self.metrics["usage"]:
            print(f"\n{BOLD + BLUE}PLUGIN USAGE{RESET}")
            print("-" * 80)
            plugins = self.metrics["usage"]["plugins"]
            total_plugin_usage = sum(plugins.values())

            for plugin, count in sorted(plugins.items(), key=lambda x: -x[1])[:5]:
                percentage = (count / total_plugin_usage * 100) if total_plugin_usage > 0 else 0
                bar = progress_bar(count, max(plugins.values()), width=30)
                print(f"  {plugin:30} {count:4} [{bar}] {percentage:5.1f}%")

        # Error severity breakdown
        if "errors" in self.metrics:
            error_metrics = self.metrics["errors"].get("metrics", {})
            by_severity = error_metrics.get("by_severity", {})

            if by_severity:
                print(f"\n{BOLD + BLUE}ERROR SEVERITY{RESET}")
                print("-" * 80)

                severity_colors = {
                    "critical": RED,
                    "high": YELLOW,
                    "medium": BLUE,
                    "low": GREEN,
                }

                total_errors = sum(by_severity.values())
                for severity in ["critical", "high", "medium", "low"]:
                    count = by_severity.get(severity, 0)
                    percentage = (count / total_errors * 100) if total_errors > 0 else 0
                    color = severity_colors.get(severity, RESET)
                    bar = progress_bar(count, max(by_severity.values()), width=30)
                    print(f"  {color}{severity.capitalize():12}{RESET} {count:4} [{bar}] {percentage:5.1f}%")

        print("\n" + BOLD + CYAN + "=" * 80 + RESET)
        print()

    def generate_html_report(self, output_file: str = "dashboard.html") -> str:
        """Generate an HTML report with visualizations."""
        kpis = self.calculate_kpis()

        def gauge_svg(value: float, target: float, label: str, max_value: float = 100) -> str:
            """Generate SVG gauge chart."""
            # Simple gauge using arc path
            percentage = min(value / max_value, 1.0)
            target_percentage = min(target / max_value, 1.0)

            # Determine color based on target
            if value >= target:
                color = "#10b981"  # green
            elif value >= target * 0.8:
                color = "#f59e0b"  # yellow
            else:
                color = "#ef4444"  # red

            angle = percentage * 180
            angle_rad = (angle - 90) * (math.pi / 180)
            x = 100 + 80 * math.cos(angle_rad)
            y = 100 + 80 * math.sin(angle_rad)

            # Target indicator
            target_angle = target_percentage * 180
            target_angle_rad = (target_angle - 90) * (math.pi / 180)
            target_x = 100 + 85 * math.cos(target_angle_rad)
            target_y = 100 + 85 * math.sin(target_angle_rad)

            return f"""
            <svg viewBox="0 0 200 120" class="gauge">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e5e7eb" stroke-width="20" stroke-linecap="round"/>
                <path d="M 20 100 A 80 80 0 0 1 {x} {y}" fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round"/>
                <circle cx="{target_x}" cy="{target_y}" r="4" fill="#6366f1"/>
                <text x="100" y="90" text-anchor="middle" class="gauge-value">{value:.1f}</text>
                <text x="100" y="110" text-anchor="middle" class="gauge-label">{label}</text>
            </svg>
            """

        def bar_chart(data: Dict[str, int], title: str) -> str:
            """Generate simple bar chart."""
            if not data:
                return "<p>No data available</p>"

            max_value = max(data.values())
            bars = ""

            for label, value in sorted(data.items(), key=lambda x: -x[1])[:10]:
                percentage = (value / max_value * 100) if max_value > 0 else 0
                bars += f"""
                <div class="bar-item">
                    <div class="bar-label">{label}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%"></div>
                        <div class="bar-value">{value}</div>
                    </div>
                </div>
                """

            return f"""
            <div class="chart">
                <h3>{title}</h3>
                <div class="bar-chart">{bars}</div>
            </div>
            """

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Healing Knowledge Base Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f3f4f6;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #111827;
        }}
        .subtitle {{
            color: #6b7280;
            margin-bottom: 30px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .kpi-card {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #6366f1;
        }}
        .kpi-card h3 {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #111827;
        }}
        .kpi-target {{
            font-size: 0.9em;
            color: #6b7280;
            margin-top: 5px;
        }}
        .gauge {{
            width: 100%;
            height: auto;
        }}
        .gauge-value {{
            font-size: 24px;
            font-weight: bold;
            fill: #111827;
        }}
        .gauge-label {{
            font-size: 12px;
            fill: #6b7280;
        }}
        .chart {{
            margin: 30px 0;
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }}
        .chart h3 {{
            margin-bottom: 20px;
            color: #111827;
        }}
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .bar-item {{
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 10px;
            align-items: center;
        }}
        .bar-label {{
            font-size: 0.9em;
            color: #4b5563;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .bar-container {{
            position: relative;
            height: 30px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            transition: width 0.3s ease;
        }}
        .bar-value {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-weight: bold;
            font-size: 0.9em;
            color: #1f2937;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .status-success {{ background: #d1fae5; color: #065f46; }}
        .status-warning {{ background: #fef3c7; color: #92400e; }}
        .status-error {{ background: #fee2e2; color: #991b1b; }}
        .metrics-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }}
        .metric-box {{
            background: white;
            border: 1px solid #e5e7eb;
            padding: 15px;
            border-radius: 6px;
        }}
        .metric-box h4 {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 5px;
        }}
        .metric-box .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #111827;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Self-Healing Knowledge Base Dashboard</h1>
        <p class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Key Performance Indicators</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                {gauge_svg(kpis['triage_accuracy'], self.targets['triage_accuracy'], 'Triage Accuracy')}
                <div class="kpi-target">Target: {self.targets['triage_accuracy']:.0f}%+</div>
            </div>
            <div class="kpi-card">
                {gauge_svg(kpis['high_confidence_rate'], self.targets['high_confidence_rate'], 'High-Confidence', 100)}
                <div class="kpi-target">Target: {self.targets['high_confidence_rate']:.0f}%+</div>
            </div>
            <div class="kpi-card">
                {gauge_svg(kpis['pr_merge_rate'], self.targets['pr_merge_rate'], 'PR Merge Rate', 100)}
                <div class="kpi-target">Target: {self.targets['pr_merge_rate']:.0f}%+</div>
            </div>
            <div class="kpi-card">
                {gauge_svg(kpis['time_saved_monthly'], self.targets['time_saved_monthly'], 'Time Saved (hrs)', 30)}
                <div class="kpi-target">Target: {self.targets['time_saved_monthly']:.0f}+ hours</div>
            </div>
        </div>

        <h2>Additional Metrics</h2>
        <div class="metrics-summary">
            <div class="metric-box">
                <h4>Error Resolution Rate</h4>
                <div class="value">{kpis['error_resolution_rate']:.1f}%</div>
            </div>
            <div class="metric-box">
                <h4>Total Events</h4>
                <div class="value">{kpis['total_events']}</div>
            </div>
            <div class="metric-box">
                <h4>Plugin Usage</h4>
                <div class="value">{kpis['plugin_usage']}</div>
            </div>
            <div class="metric-box">
                <h4>Total Errors</h4>
                <div class="value">{kpis['total_errors']}</div>
            </div>
        </div>
        """

        # Add plugin usage chart
        if "usage" in self.metrics and "plugins" in self.metrics["usage"]:
            html_content += bar_chart(self.metrics["usage"]["plugins"], "Plugin Usage")

        # Add error severity chart
        if "errors" in self.metrics:
            error_metrics = self.metrics["errors"].get("metrics", {})
            by_severity = error_metrics.get("by_severity", {})
            if by_severity:
                html_content += bar_chart(by_severity, "Error Severity Distribution")

        html_content += """
        <footer>
            <p>Self-Healing Knowledge Base Metrics Dashboard</p>
            <p>Targets: Triage Accuracy 80%+ | High-Confidence 50%+ | PR Merge Rate 70%+ | Time Saved 15+ hrs/month</p>
        </footer>
    </div>
</body>
</html>
        """

        output_path = self.data_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\nHTML report generated: {output_path}")
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate dashboard for self-healing knowledge base metrics"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./metrics-output",
        help="Directory containing metrics data (default: ./metrics-output)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["terminal", "html", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dashboard.html",
        help="HTML output filename (default: dashboard.html)"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Generate simulated metrics for testing"
    )

    args = parser.parse_args()

    dashboard = MetricsDashboard(data_dir=args.data_dir)

    if args.simulate:
        dashboard.simulate_metrics()
    else:
        dashboard.load_metrics()

    if args.format in ["terminal", "both"]:
        dashboard.print_terminal_dashboard()

    if args.format in ["html", "both"]:
        dashboard.generate_html_report(args.output)

    return 0


if __name__ == "__main__":
    exit(main())
