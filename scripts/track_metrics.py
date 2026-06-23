#!/usr/bin/env python3
"""
🛡️ Aegis Box - Metrics Tracker Dashboard

战况监控雷达 - 实时追踪 Aegis Box 的社区增长和影响力

Usage:
    python scripts/track_metrics.py
    python scripts/track_metrics.py --json  # 输出 JSON 格式

Requirements:
    pip install rich requests
"""

import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich import box
except ImportError:
    print("❌ 缺少依赖库")
    print("请运行: pip install rich requests")
    sys.exit(1)

console = Console()


class AegisMetricsTracker:
    """Aegis Box 指标追踪器"""

    def __init__(self):
        self.github_repo = "dingwencheng9/aegis-box"
        self.pypi_package = "aegis-box"
        self.metrics: Dict[str, Any] = {}

    def fetch_github_metrics(self) -> Dict[str, Any]:
        """获取 GitHub 指标"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "watchers": data.get("subscribers_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "created_at": data.get("created_at", "Unknown"),
                "updated_at": data.get("updated_at", "Unknown"),
            }
        except requests.RequestException as e:
            console.print(f"[yellow]⚠️  GitHub API 请求失败: {e}[/yellow]")
            return {}

    def fetch_github_issues(self) -> Dict[str, int]:
        """获取 GitHub Issues 详细统计"""
        try:
            # Open issues
            url = f"https://api.github.com/repos/{self.github_repo}/issues?state=open&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            open_issues = [i for i in response.json() if "pull_request" not in i]

            # Closed issues
            url = f"https://api.github.com/repos/{self.github_repo}/issues?state=closed&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            closed_issues = [i for i in response.json() if "pull_request" not in i]

            return {
                "open": len(open_issues),
                "closed": len(closed_issues),
                "total": len(open_issues) + len(closed_issues),
            }
        except requests.RequestException as e:
            console.print(f"[yellow]⚠️  GitHub Issues API 请求失败: {e}[/yellow]")
            return {"open": 0, "closed": 0, "total": 0}

    def fetch_github_prs(self) -> Dict[str, int]:
        """获取 GitHub Pull Requests 统计"""
        try:
            # Open PRs
            url = f"https://api.github.com/repos/{self.github_repo}/pulls?state=open&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            open_prs = response.json()

            # Closed PRs (includes merged)
            url = f"https://api.github.com/repos/{self.github_repo}/pulls?state=closed&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            closed_prs = response.json()

            merged_prs = [pr for pr in closed_prs if pr.get("merged_at")]

            return {
                "open": len(open_prs),
                "merged": len(merged_prs),
                "closed_unmerged": len(closed_prs) - len(merged_prs),
                "total": len(open_prs) + len(closed_prs),
            }
        except requests.RequestException as e:
            console.print(f"[yellow]⚠️  GitHub PRs API 请求失败: {e}[/yellow]")
            return {"open": 0, "merged": 0, "closed_unmerged": 0, "total": 0}

    def fetch_pypi_metrics(self) -> Dict[str, Any]:
        """获取 PyPI 指标"""
        try:
            # 获取包信息
            url = f"https://pypi.org/pypi/{self.pypi_package}/json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            info = data.get("info", {})
            releases = data.get("releases", {})

            # 获取下载量（使用 pypistats API）
            # 注意：pypistats.org 的 API 可能有延迟
            downloads = self._fetch_pypi_downloads()

            return {
                "version": info.get("version", "Unknown"),
                "author": info.get("author", "Unknown"),
                "license": info.get("license", "Unknown"),
                "release_count": len(releases),
                "downloads_last_day": downloads.get("last_day", "N/A"),
                "downloads_last_week": downloads.get("last_week", "N/A"),
                "downloads_last_month": downloads.get("last_month", "N/A"),
            }
        except requests.RequestException as e:
            console.print(f"[yellow]⚠️  PyPI API 请求失败: {e}[/yellow]")
            return {}

    def _fetch_pypi_downloads(self) -> Dict[str, Any]:
        """获取 PyPI 下载量"""
        try:
            url = f"https://pypistats.org/api/packages/{self.pypi_package}/recent"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "last_day": data.get("data", {}).get("last_day", "N/A"),
                "last_week": data.get("data", {}).get("last_week", "N/A"),
                "last_month": data.get("data", {}).get("last_month", "N/A"),
            }
        except requests.RequestException:
            # pypistats API 可能在包刚发布时不可用
            return {"last_day": "N/A", "last_week": "N/A", "last_month": "N/A"}

    def collect_all_metrics(self) -> Dict[str, Any]:
        """收集所有指标"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("📊 获取 GitHub 仓库数据...", total=None)
            github_metrics = self.fetch_github_metrics()
            progress.update(task1, completed=True)

            task2 = progress.add_task("🐛 获取 GitHub Issues 数据...", total=None)
            issues_metrics = self.fetch_github_issues()
            progress.update(task2, completed=True)

            task3 = progress.add_task("🔀 获取 GitHub PRs 数据...", total=None)
            prs_metrics = self.fetch_github_prs()
            progress.update(task3, completed=True)

            task4 = progress.add_task("📦 获取 PyPI 包数据...", total=None)
            pypi_metrics = self.fetch_pypi_metrics()
            progress.update(task4, completed=True)

        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "github": github_metrics,
            "github_issues": issues_metrics,
            "github_prs": prs_metrics,
            "pypi": pypi_metrics,
        }

        return self.metrics

    def render_dashboard(self):
        """渲染终端仪表盘"""
        if not self.metrics:
            console.print("[red]❌ 没有可用的指标数据[/red]")
            return

        # 创建布局
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Header
        header = Panel(
            "[bold cyan]🛡️  AEGIS BOX - METRICS DASHBOARD[/bold cyan]",
            box=box.DOUBLE,
            style="bold cyan",
        )
        layout["header"].update(header)

        # Body - 分成两列
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        # Left Column - GitHub Stats
        github_table = Table(
            title="📊 GitHub Statistics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        github_table.add_column("Metric", style="cyan", width=20)
        github_table.add_column("Value", style="green", justify="right")

        gh = self.metrics.get("github", {})
        github_table.add_row("⭐ Stars", str(gh.get("stars", 0)))
        github_table.add_row("🍴 Forks", str(gh.get("forks", 0)))
        github_table.add_row("👀 Watchers", str(gh.get("watchers", 0)))
        github_table.add_row("🐛 Open Issues", str(gh.get("open_issues", 0)))

        # Issues breakdown
        issues = self.metrics.get("github_issues", {})
        github_table.add_row("", "")  # Separator
        github_table.add_row("[bold]Issues Detail[/bold]", "")
        github_table.add_row("  Open", str(issues.get("open", 0)))
        github_table.add_row("  Closed", str(issues.get("closed", 0)))
        github_table.add_row("  Total", str(issues.get("total", 0)))

        # PRs breakdown
        prs = self.metrics.get("github_prs", {})
        github_table.add_row("", "")  # Separator
        github_table.add_row("[bold]Pull Requests[/bold]", "")
        github_table.add_row("  Open", str(prs.get("open", 0)))
        github_table.add_row("  Merged", f"[green]{prs.get('merged', 0)}[/green]")
        github_table.add_row("  Closed (not merged)", str(prs.get("closed_unmerged", 0)))

        layout["left"].update(Panel(github_table, border_style="cyan"))

        # Right Column - PyPI Stats
        pypi_table = Table(
            title="📦 PyPI Statistics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow",
        )
        pypi_table.add_column("Metric", style="cyan", width=20)
        pypi_table.add_column("Value", style="green", justify="right")

        pypi = self.metrics.get("pypi", {})
        pypi_table.add_row("📌 Version", str(pypi.get("version", "Unknown")))
        pypi_table.add_row("📜 License", str(pypi.get("license", "Unknown")))
        pypi_table.add_row("🎯 Total Releases", str(pypi.get("release_count", 0)))
        pypi_table.add_row("", "")  # Separator
        pypi_table.add_row("[bold]Downloads[/bold]", "")
        pypi_table.add_row("  Last 24h", str(pypi.get("downloads_last_day", "N/A")))
        pypi_table.add_row("  Last 7 days", str(pypi.get("downloads_last_week", "N/A")))
        pypi_table.add_row("  Last 30 days", str(pypi.get("downloads_last_month", "N/A")))

        layout["right"].update(Panel(pypi_table, border_style="yellow"))

        # Footer
        timestamp = self.metrics.get("timestamp", "Unknown")
        footer = Panel(
            f"[dim]Last updated: {timestamp} | Repository: {self.github_repo} | Package: {self.pypi_package}[/dim]",
            box=box.SIMPLE,
        )
        layout["footer"].update(footer)

        # Render
        console.print(layout)

    def export_json(self) -> str:
        """导出为 JSON 格式"""
        return json.dumps(self.metrics, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Aegis Box Metrics Tracker - 战况监控雷达"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式（适合程序化处理）",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="保存指标到文件",
    )
    args = parser.parse_args()

    console.print("\n[bold cyan]🛡️  AEGIS BOX - METRICS TRACKER[/bold cyan]\n")

    tracker = AegisMetricsTracker()
    tracker.collect_all_metrics()

    if args.json:
        output = tracker.export_json()
        console.print(output)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            console.print(f"\n[green]✅ 指标已保存到: {args.output}[/green]")
    else:
        tracker.render_dashboard()

        if args.output:
            with open(args.output, "w") as f:
                f.write(tracker.export_json())
            console.print(f"\n[green]✅ 指标已保存到: {args.output}[/green]")

    console.print("\n[bold green]✅ 战况监控完成！[/bold green]\n")


if __name__ == "__main__":
    main()
