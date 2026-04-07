"""Command-line interface for WCAG Auditor."""
import click
import re
import sys
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from wcag_auditor.auditor import Auditor
from wcag_auditor.reporter import Reporter
from wcag_auditor.user_pass import UserPassConfigError, UserPassRunner, load_user_pass_config
from wcag_auditor import DEFAULT_USER_AGENT, __version__

console = Console()

@click.group()
@click.version_option(version=__version__, prog_name="wcag-auditor")
def cli():
    """WCAG Auditor - Audit websites for WCAG 2.2 compliance."""
    pass

@cli.command()
@click.argument("url")
@click.option("--depth", "-d", default=2, help="Maximum crawl depth (default: 2)")
@click.option("--max-pages", "-m", default=50, help="Maximum number of pages to audit (default: 50)")
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "html", "markdown", "text", "vpat"]), default="text", help="Output format (default: text)")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
@click.option("--user-agent", "-u", default=DEFAULT_USER_AGENT, help="User agent string for requests")
@click.option("--user-pass", is_flag=True, help="Run synthetic reviewers and a copywriter using OpenRouter models from env vars or .env")
@click.option("--env-file", default=".env", show_default=True, help="Environment file used to resolve optional OpenRouter user-pass settings")
@click.option(
    "--sample-strategy",
    type=click.Choice(["representative", "sequential"]),
    default="representative",
    help="Page sampling strategy for site-level reporting (default: representative)",
)
def audit(
    url: str,
    depth: int,
    max_pages: int,
    output_format: str,
    output: Optional[str],
    timeout: int,
    user_agent: str,
    user_pass: bool,
    env_file: str,
    sample_strategy: str,
):
    """Audit a website for WCAG 2.2 compliance."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Auditing website...", total=None)
            
            auditor = Auditor(
                base_url=url,
                max_depth=depth,
                max_pages=max_pages,
                timeout=timeout,
                user_agent=user_agent,
                sample_strategy=sample_strategy,
            )
            
            results = auditor.audit()
            report_input = dict(results)

            if user_pass:
                progress.update(task, description="Running synthetic user pass...")
                try:
                    config = load_user_pass_config(env_file)
                    runner = UserPassRunner(config)
                    report_input["user_pass"] = runner.run(results)
                except UserPassConfigError as exc:
                    runner = None
                    report_input["user_pass"] = {
                        "status": "error",
                        "provider": "openrouter",
                        "pages_reviewed": 0,
                        "agents": [],
                        "findings": [],
                        "themes": [],
                        "rewrite_suggestions": [],
                        "errors": [{"stage": "config", "message": str(exc)}],
                        "limitations": [
                            "Synthetic reviewers are optional and require explicit OpenRouter configuration.",
                            "Synthetic user-pass output does not replace disabled human participants.",
                        ],
                    }
            else:
                runner = None

            progress.update(task, description="Generating report...")
            
            reporter = Reporter(report_input)
            report = reporter.generate(output_format)

            # Always save a markdown report to ./reports/
            progress.update(task, description="Saving report...")
            report_path = _save_report(reporter, url)

            # Generate executive report if user-pass runner is available
            if runner is not None:
                progress.update(task, description="Generating executive report...")
                try:
                    exec_data = runner.generate_executive_report(report_input)
                    _save_executive_report(exec_data, url, report_path.name)
                except Exception as exc:
                    console.print("[yellow]Executive report failed: {0}[/yellow]".format(exc))
            
            if output:
                Path(output).write_text(report, encoding="utf-8")
                console.print(f"[green]Report saved to {output}[/green]")
            else:
                if output_format == "text":
                    console.print(report)
                else:
                    print(report)
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Audit interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.argument("url")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
def check(url: str, timeout: int):
    """Check a single page for WCAG 2.2 compliance."""
    try:
        auditor = Auditor(
            base_url=url,
            max_depth=0,
            max_pages=1,
            timeout=timeout
        )
        
        results = auditor.audit()
        reporter = Reporter(results)
        
        # Generate text report for single page
        report = reporter.generate("text")
        console.print(report)
        
        # Show summary table
        violations = results.get("violations", [])
        if violations:
            violation_types = results.get("violation_types") or {}
            if not violation_types:
                for violation in violations:
                    rule = violation.get("rule", "Unknown")
                    violation_types[rule] = violation_types.get(rule, 0) + 1

            table = Table(title="WCAG Violations Summary")
            table.add_column("Rule", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            table.add_column("Impact", style="red")
            
            for rule, count in violation_types.items():
                impact = next(
                    (violation.get("impact", "Unknown") for violation in violations if violation.get("rule") == rule),
                    "Unknown",
                )
                table.add_row(
                    rule,
                    str(count),
                    impact,
                )
            
            console.print(table)
        else:
            console.print("[green]No WCAG violations found![/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.argument("url")
@click.option("--depth", "-d", default=1, help="Maximum crawl depth (default: 1)")
@click.option("--max-pages", "-m", default=10, help="Maximum number of pages to audit (default: 10)")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
@click.option(
    "--sample-strategy",
    type=click.Choice(["representative", "sequential"]),
    default="representative",
    help="Page sampling strategy for site-level reporting (default: representative)",
)
def summary(url: str, depth: int, max_pages: int, timeout: int, sample_strategy: str):
    """Generate a summary report of WCAG compliance."""
    try:
        auditor = Auditor(
            base_url=url,
            max_depth=depth,
            max_pages=max_pages,
            timeout=timeout,
            sample_strategy=sample_strategy,
        )
        
        results = auditor.audit()
        reporter = Reporter(results)
        
        # Generate summary statistics
        total_pages = results.get("pages_audited", 0)
        total_violations = results.get("total_violations", 0)
        total_manual_reviews = results.get("total_manual_reviews", 0)
        violation_types = results.get("violation_types", {})
        
        console.print(f"\n[bold]WCAG Audit Summary for {url}[/bold]")
        console.print(f"Pages audited: {total_pages}")
        console.print(f"Total violations: {total_violations}")
        console.print(f"Needs manual review: {total_manual_reviews}")
        
        if violation_types:
            table = Table(title="Violation Types")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            
            for vtype, count in violation_types.items():
                table.add_row(vtype, str(count))
            
            console.print(table)
        else:
            console.print("[green]No violations found![/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

def _save_report(reporter: Reporter, url: str) -> Path:
    """Save a timestamped markdown report to ./reports/."""
    # Sanitize URL into a filesystem-safe slug
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w.-]+", "_", slug).strip("_").lower()
    slug = slug[:80]  # cap length for filesystem safety

    timestamp = time.strftime("%Y%m%d-%H%M")
    filename = "{0}-{1}.md".format(slug, timestamp)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / filename

    report_path.write_text(reporter.generate("markdown"), encoding="utf-8")
    console.print("[dim]Report saved to {0}[/dim]".format(report_path))
    return report_path


def _save_executive_report(exec_data: dict, url: str, raw_report_name: str) -> None:
    """Render and save the executive report to ./reports/."""
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w.-]+", "_", slug).strip("_").lower()
    slug = slug[:80]

    timestamp = time.strftime("%Y%m%d-%H%M")
    filename = "{0}-{1}-executive.md".format(slug, timestamp)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / filename

    md = _render_executive_markdown(exec_data, url, raw_report_name)
    report_path.write_text(md, encoding="utf-8")
    console.print("[dim]Executive report saved to {0}[/dim]".format(report_path))


def _render_executive_markdown(data: dict, url: str, raw_report_name: str) -> str:
    """Assemble the executive report markdown from structured data."""
    sc = data.get("scorecard", {})
    lines = [
        "# WCAG Compliance Executive Report",
        "",
        "**Site:** {0}".format(url),
        "**Date:** {0}".format(time.strftime("%Y-%m-%d %H:%M")),
        "**Pages Audited:** {0}".format(sc.get("pages_audited", 0)),
        "**Risk Assessment:** {0}".format(data.get("risk_assessment", "unknown").upper()),
        "",
    ]

    # Executive Summary
    summary = data.get("executive_summary", "")
    if summary:
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Scorecard
    lines.append("## Compliance Scorecard")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Pages Audited | {0} |".format(sc.get("pages_audited", 0)))
    lines.append("| Total Violations | {0} |".format(sc.get("total_violations", 0)))
    lines.append("| Unique Rules Violated | {0} |".format(sc.get("unique_rules_violated", 0)))
    lines.append("| Critical Issues | {0} |".format(sc.get("critical_count", 0)))
    lines.append("| Serious Issues | {0} |".format(sc.get("serious_count", 0)))
    lines.append("| Moderate Issues | {0} |".format(sc.get("moderate_count", 0)))
    lines.append("| WCAG Level A Failures | {0} |".format(sc.get("level_a_failures", 0)))
    lines.append("| WCAG Level AA Failures | {0} |".format(sc.get("level_aa_failures", 0)))
    lines.append("| Passed Checks | {0} |".format(sc.get("total_passed", 0)))
    lines.append("| Needs Manual Review | {0} |".format(sc.get("total_manual_reviews", 0)))
    lines.append("")

    # Priority Actions
    priority_actions = data.get("priority_actions", [])
    if priority_actions:
        lines.append("## Priority Action Plan")
        lines.append("")
        icons = {"P1": "\U0001f534", "P2": "\U0001f7e1", "P3": "\U0001f7e2"}
        for action in priority_actions:
            if not isinstance(action, dict):
                continue
            priority = str(action.get("priority", "P3"))
            icon = icons.get(priority, "\u26aa")
            rule = action.get("rule", "unknown")
            lines.append("### {0} {1}: {2}".format(icon, priority, rule))
            lines.append("")
            what_text = action.get("what", "")
            if what_text:
                lines.append("**What:** {0}".format(what_text))
                lines.append("")
            why_text = action.get("why", "")
            if why_text:
                lines.append("**Why:** {0}".format(why_text))
                lines.append("")
            fix_text = action.get("fix", "")
            if fix_text:
                lines.append("**Fix:**")
                lines.append("")
                lines.append(fix_text)
                lines.append("")

    # Quick Wins
    quick_wins = data.get("quick_wins", [])
    if quick_wins:
        lines.append("## Quick Wins")
        lines.append("")
        for win in quick_wins:
            if isinstance(win, str) and win.strip():
                lines.append("- {0}".format(win.strip()))
        lines.append("")

    # Synthetic Reviewer Insights (screen reader + cognitive agents)
    insights = data.get("synthetic_reviewer_insights", [])
    if insights:
        lines.append("## Synthetic Reviewer Insights")
        lines.append("")
        lines.append("*These findings come from simulated screen-reader and cognitive-load reviewers "
                      "examining representative pages.*")
        lines.append("")
        for insight in insights:
            if not isinstance(insight, dict):
                continue
            agents = ", ".join(insight.get("agent_ids", []))
            confidence = insight.get("confidence", 0.0)
            lines.append("### {0}".format(insight.get("target_text", "General")))
            lines.append("")
            lines.append("- **Category:** {0}".format(insight.get("category", "general")))
            lines.append("- **Reviewers:** {0}".format(agents))
            lines.append("- **Confidence:** {0:.0%}".format(confidence))
            issue = insight.get("issue", "")
            if issue:
                lines.append("- **Issue:** {0}".format(issue))
            change = insight.get("suggested_change", "")
            if change:
                lines.append("- **Suggested Change:** {0}".format(change))
            page = insight.get("page_url", "")
            if page:
                lines.append("- **Page:** {0}".format(page))
            lines.append("")

    # Recommended Copy Changes (copywriter agent)
    rewrites = data.get("rewrite_suggestions", [])
    if rewrites:
        lines.append("## Recommended Copy Changes")
        lines.append("")
        lines.append("*These suggestions come from a semantic and inclusive copywriter review.*")
        lines.append("")
        lines.append("| Location | Current Text | Proposed Text | Rationale |")
        lines.append("|----------|-------------|---------------|-----------|")
        for rewrite in rewrites:
            if not isinstance(rewrite, dict):
                continue
            location = str(rewrite.get("location", "")).replace("|", "\\|")
            current = str(rewrite.get("current_text", "")).replace("|", "\\|")
            proposed = str(rewrite.get("proposed_text", "")).replace("|", "\\|")
            rationale = str(rewrite.get("rationale", "")).replace("|", "\\|")
            lines.append("| {0} | {1} | {2} | {3} |".format(location, current, proposed, rationale))
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This report was generated by wcag-auditor with AI analysis via OpenRouter.*")
    lines.append("*Raw findings: {0}*".format(raw_report_name))
    lines.append("")

    return "\n".join(lines)


def main():
    cli()

if __name__ == "__main__":
    main()
