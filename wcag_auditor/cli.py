import csv
import hashlib
import json
import click
import re
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from wcag_auditor.auditor import Auditor
from wcag_auditor.reporter import Reporter
from wcag_auditor.user_pass import UserPassConfigError, UserPassRunner, load_user_pass_config
from wcag_auditor import DEFAULT_USER_AGENT, __version__

console = Console(stderr=True)

@click.group()
@click.version_option(version=__version__, prog_name="wcag-auditor")
def cli():
    """WCAG Auditor - Audit websites for WCAG 2.2 compliance."""
    pass

@cli.command()
@click.argument("url")
@click.option("--depth", "-d", default=2, help="Maximum crawl depth (default: 2)")
@click.option("--max-pages", "-m", default=50, help="Maximum number of pages to audit (default: 50)")
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "html", "markdown", "text", "vpat", "sarif"]), default="text", help="Output format (default: text)")
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
@click.option("--storage-state", type=click.Path(exists=True), help="Path to Playwright storage state JSON file")
@click.option("--include", "-i", "includes", multiple=True, help="Glob or regex URL pattern to include in the crawl (repeatable)")
@click.option("--exclude", "-x", "excludes", multiple=True, help="Glob or regex URL pattern to exclude from the crawl (repeatable)")
@click.option("--delay", type=int, default=0, help="Delay in milliseconds between page requests (default: 0)")
@click.option("--max-findings-per-rule", type=click.IntRange(min=1), default=20, show_default=True, help="Maximum findings retained per rule on each page")
@click.option("--respect-robots/--no-respect-robots", default=True, help="Respect robots.txt settings (default: True)")
@click.option("--fail-on", type=click.Choice(["minor", "moderate", "serious", "critical"]), help="Exit with code 1 if violations at or above this impact exist")
@click.option("--baseline", type=click.Path(), help="Path to baseline JSON file for known issues suppression")
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
    storage_state: Optional[str],
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    delay: int,
    max_findings_per_rule: int,
    respect_robots: bool,
    fail_on: Optional[str],
    baseline: Optional[str],
):
    """Audit a website for WCAG 2.2 compliance."""
    try:
        # Load baseline if it exists
        baseline_fingerprints = set()
        if baseline and Path(baseline).exists():
            try:
                baseline_data = json.loads(Path(baseline).read_text(encoding="utf-8"))
                if isinstance(baseline_data, list):
                    for item in baseline_data:
                        if isinstance(item, dict) and "fingerprint" in item:
                            baseline_fingerprints.add(item["fingerprint"])
            except Exception as exc:
                console.print(f"[yellow]Warning: Could not load baseline: {exc}[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Auditing website...", total=None)

            auditor = Auditor(
                base_url=url,
                max_depth=depth,
                max_pages=max_pages,
                timeout=timeout,
                user_agent=user_agent,
                sample_strategy=sample_strategy,
                storage_state=storage_state,
                includes=list(includes),
                excludes=list(excludes),
                delay=delay,
                max_findings_per_rule=max_findings_per_rule,
                respect_robots=respect_robots
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

            # Process baseline suppression
            violations = report_input.get("violations", [])
            manual_reviews = report_input.get("manual_reviews", [])

            known_issues = []
            active_violations = []
            active_reviews = []

            def compute_fingerprint(finding: Dict[str, Any]) -> str:
                rule = finding.get("rule", "unknown")
                template = finding.get("page_template", "/")
                selector = finding.get("selector", "unknown")
                key = f"{rule}:{template}:{selector}"
                return hashlib.sha256(key.encode("utf-8")).hexdigest()

            for finding in violations:
                fp = compute_fingerprint(finding)
                finding["fingerprint"] = fp
                if fp in baseline_fingerprints:
                    finding["suppressed"] = True
                    known_issues.append(finding)
                else:
                    active_violations.append(finding)

            for finding in manual_reviews:
                fp = compute_fingerprint(finding)
                finding["fingerprint"] = fp
                if fp in baseline_fingerprints:
                    finding["suppressed"] = True
                    known_issues.append(finding)
                else:
                    active_reviews.append(finding)

            # Update report input with active and known issues
            report_input["violations"] = active_violations
            report_input["manual_reviews"] = active_reviews
            report_input["known_issues"] = known_issues
            report_input["total_violations"] = len(active_violations)
            report_input["total_manual_reviews"] = len(active_reviews)

            # Recalculate violation counts
            violation_types = {}
            for f in active_violations:
                r = f.get("rule")
                if r:
                    violation_types[r] = violation_types.get(r, 0) + 1
            report_input["violation_types"] = violation_types

            manual_review_types = {}
            for f in active_reviews:
                r = f.get("rule")
                if r:
                    manual_review_types[r] = manual_review_types.get(r, 0) + 1
            report_input["manual_review_types"] = manual_review_types

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

            # Check execution failures
            for warning in report_input.get("warnings", []):
                if warning.get("rule") == "execution-failure":
                    console.print("[red]Execution failure detected.[/red]")
                    sys.exit(2)

            # Check fail-on threshold
            if fail_on and report_input["total_violations"] > 0:
                IMPACT_SEVERITY = {"minor": 1, "moderate": 2, "serious": 3, "critical": 4}
                threshold = IMPACT_SEVERITY.get(fail_on, 1)
                for f in active_violations:
                    imp = f.get("impact", "moderate")
                    if IMPACT_SEVERITY.get(imp, 1) >= threshold:
                        console.print(f"[red]Failure: Found violation with impact '{imp}' at or above threshold '{fail_on}'[/red]")
                        sys.exit(1)

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

@cli.command("generate-coverage")
@click.option("--output", "-o", default="docs/coverage.md", help="Output path for coverage matrix")
def generate_coverage_cmd(output: str):
    """Generate WCAG 2.2 Coverage Matrix from rule metadata."""
    from wcag_auditor.rules.core_rules import get_core_rules
    from wcag_auditor.reporter import WCAG_22_AA_CRITERIA

    rules = get_core_rules()

    lines = [
        "# WCAG 2.2 Level A/AA Coverage Matrix",
        "",
        "This matrix lists all WCAG 2.2 Level A and AA Success Criteria, showing the coverage type and the specific rule(s) implemented in `wcag-auditor`.",
        "",
        "| Criteria | Name | Level | Coverage Type | Implemented Rule(s) |",
        "|---|---|---|---|---|",
    ]

    for wcag, info in sorted(WCAG_22_AA_CRITERIA.items(), key=lambda x: [int(c) for c in x[0].split('.')]):
        matching_rules = [r for r in rules if r.metadata.wcag_criterion == wcag]

        if not matching_rules:
            cov_type = "manual-only"
            rules_str = "N/A"
        else:
            cov_types = {getattr(r.metadata, "coverage_type", "automated") for r in matching_rules}
            if "partial-heuristic" in cov_types or ("automated" in cov_types and "needs-review-only" in cov_types):
                cov_type = "partial-heuristic"
            elif "needs-review-only" in cov_types:
                cov_type = "needs-review-only"
            else:
                cov_type = "automated"
            rules_str = ", ".join(f"`{r.metadata.id}`" for r in matching_rules)

        lines.append(f"| {wcag} | {info['name']} | {info['level']} | {cov_type} | {rules_str} |")

    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green]Coverage matrix saved to {output}[/green]")

@cli.group()
def baseline():
    """Manage audit baselines for CI."""
    pass

@baseline.command("update")
@click.argument("url")
@click.option("--depth", "-d", default=2, help="Maximum crawl depth (default: 2)")
@click.option("--max-pages", "-m", default=50, help="Maximum number of pages to audit (default: 50)")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
@click.option("--user-agent", "-u", default=DEFAULT_USER_AGENT, help="User agent string for requests")
@click.option(
    "--sample-strategy",
    type=click.Choice(["representative", "sequential"]),
    default="representative",
    help="Page sampling strategy for site-level reporting (default: representative)",
)
@click.option("--output", "-o", default="baseline.json", help="Path to save the baseline file (default: baseline.json)")
@click.option("--storage-state", type=click.Path(exists=True), help="Path to Playwright storage state JSON file")
@click.option("--include", "-i", "includes", multiple=True, help="Glob or regex URL pattern to include (repeatable)")
@click.option("--exclude", "-x", "excludes", multiple=True, help="Glob or regex URL pattern to exclude (repeatable)")
@click.option("--delay", type=int, default=0, help="Delay in milliseconds between page requests (default: 0)")
@click.option("--max-findings-per-rule", type=click.IntRange(min=1), default=20, show_default=True, help="Maximum findings retained per rule on each page")
@click.option("--respect-robots/--no-respect-robots", default=True, help="Respect robots.txt settings (default: True)")
def baseline_update(
    url: str,
    depth: int,
    max_pages: int,
    timeout: int,
    user_agent: str,
    sample_strategy: str,
    output: str,
    storage_state: Optional[str],
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    delay: int,
    max_findings_per_rule: int,
    respect_robots: bool,
):
    """Run audit and save all current violations to a baseline file."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Auditing for baseline...", total=None)

            auditor = Auditor(
                base_url=url,
                max_depth=depth,
                max_pages=max_pages,
                timeout=timeout,
                user_agent=user_agent,
                sample_strategy=sample_strategy,
                storage_state=storage_state,
                includes=list(includes),
                excludes=list(excludes),
                delay=delay,
                max_findings_per_rule=max_findings_per_rule,
                respect_robots=respect_robots
            )

            results = auditor.audit()

            # Check execution failures
            for warning in results.get("warnings", []):
                if warning.get("rule") == "execution-failure":
                    console.print("[red]Execution failure detected. Baseline update aborted.[/red]")
                    sys.exit(2)

            violations = results.get("violations", [])
            manual_reviews = results.get("manual_reviews", [])

            baseline_list = []

            def compute_fingerprint(finding: Dict[str, Any]) -> str:
                rule = finding.get("rule", "unknown")
                template = finding.get("page_template", "/")
                selector = finding.get("selector", "unknown")
                key = f"{rule}:{template}:{selector}"
                return hashlib.sha256(key.encode("utf-8")).hexdigest()

            for finding in violations + manual_reviews:
                fp = compute_fingerprint(finding)
                baseline_list.append({
                    "rule": finding.get("rule", "unknown"),
                    "page_template": finding.get("page_template", "/"),
                    "selector": finding.get("selector", "unknown"),
                    "fingerprint": fp
                })

            # Write to output file
            Path(output).write_text(json.dumps(baseline_list, indent=2) + "\n", encoding="utf-8")
            console.print(f"[green]Successfully saved {len(baseline_list)} issues to baseline file: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating baseline: {e}[/red]")
        sys.exit(1)

@cli.group()
def review():
    """Manage manual review workflows."""
    pass

@review.command("export")
@click.argument("audit_json", type=click.Path(exists=True))
@click.option("--format", "-f", "output_format", type=click.Choice(["csv", "md"]), default="csv", help="Output format (default: csv)")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: reviewed_checklist.csv/md)")
def review_export(audit_json: str, output_format: str, output: Optional[str]):
    """Export needs-review findings to a CSV or Markdown checklist."""
    try:
        audit_data = json.loads(Path(audit_json).read_text(encoding="utf-8"))
        manual_reviews = audit_data.get("manual_reviews", [])

        if not manual_reviews:
            console.print("[yellow]No manual reviews found in audit file.[/yellow]")
            return

        default_out = output or (f"reviewed_checklist.csv" if output_format == "csv" else "reviewed_checklist.md")

        if output_format == "csv":
            with open(default_out, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["finding_id", "page", "wcag", "element", "evidence", "verdict (pass/fail/n-a)", "reviewer", "notes"])
                for idx, finding in enumerate(manual_reviews, 1):
                    fid = finding.get("fingerprint") or f"review-{idx}"
                    writer.writerow([
                        fid,
                        finding.get("page_url", "unknown"),
                        finding.get("wcag", "unknown"),
                        finding.get("element", "unknown"),
                        finding.get("message", ""),
                        "",
                        "",
                        ""
                    ])
            console.print(f"[green]Exported {len(manual_reviews)} review items to CSV: {default_out}[/green]")

        else:
            lines = [
                "# WCAG Audit Manual Review Checklist",
                "",
                "Please fill in the **Verdict** column with `pass`, `fail`, or `n-a`, and fill in the reviewer and notes.",
                "",
                "| Finding ID | Page | WCAG | Element | Evidence | Verdict (pass/fail/n-a) | Reviewer | Notes |",
                "|---|---|---|---|---|---|---|---|",
            ]
            for idx, finding in enumerate(manual_reviews, 1):
                fid = finding.get("fingerprint") or f"review-{idx}"
                page = finding.get("page_url", "unknown")
                wcag = finding.get("wcag", "unknown")
                element = finding.get("element", "unknown").replace("|", "\\|").replace("\n", " ")
                evidence = finding.get("message", "").replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {fid} | {page} | {wcag} | `{element}` | {evidence} | | | |")

            Path(default_out).write_text("\n".join(lines) + "\n", encoding="utf-8")
            console.print(f"[green]Exported {len(manual_reviews)} review items to Markdown: {default_out}[/green]")

    except Exception as e:
        console.print(f"[red]Error exporting review checklist: {e}[/red]")
        sys.exit(1)


@review.command("merge")
@click.argument("audit_json", type=click.Path(exists=True))
@click.argument("reviewed_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output JSON path (default: overwrite audit_json)")
def review_merge(audit_json: str, reviewed_file: str, output: Optional[str]):
    """Merge completed review checklist back into the audit JSON, updating conformance."""
    try:
        audit_data = json.loads(Path(audit_json).read_text(encoding="utf-8"))
        manual_reviews = audit_data.get("manual_reviews", [])
        violations = audit_data.get("violations", [])
        passed = audit_data.get("passed", [])

        # Build map of reviews by ID
        reviews_map = {}
        for idx, r in enumerate(manual_reviews, 1):
            fid = r.get("fingerprint") or f"review-{idx}"
            reviews_map[fid] = r

        verdicts = {}

        # Determine format
        if reviewed_file.endswith(".csv"):
            with open(reviewed_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fid = row.get("finding_id")
                    verdict = (row.get("verdict (pass/fail/n-a)") or row.get("verdict") or "").strip().lower()
                    if fid:
                        verdicts[fid] = {
                            "verdict": verdict,
                            "reviewer": row.get("reviewer", ""),
                            "notes": row.get("notes", "")
                        }
        else:
            content = Path(reviewed_file).read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("|") and not "Finding ID" in line and not "---|---" in line:
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 8:
                        fid = parts[0]
                        verdict = parts[5].lower()
                        reviewer = parts[6]
                        notes = parts[7]
                        verdicts[fid] = {
                            "verdict": verdict,
                            "reviewer": reviewer,
                            "notes": notes
                        }

        new_manual_reviews = []
        new_violations_count = 0
        new_passed_count = 0

        for fid, finding in reviews_map.items():
            info = verdicts.get(fid)
            if not info or not info["verdict"]:
                new_manual_reviews.append(finding)
                continue

            verdict = info["verdict"]
            finding["reviewer"] = info["reviewer"]
            finding["reviewer_notes"] = info["notes"]

            if verdict == "fail":
                finding["finding_type"] = "violation"
                violations.append(finding)
                new_violations_count += 1
            elif verdict == "pass":
                finding["finding_type"] = "passed"
                passed.append({
                    "rule": finding.get("rule", "Unknown"),
                    "description": finding.get("description", "No description"),
                    "wcag": finding.get("wcag", "Unknown"),
                    "level": finding.get("level", "Unknown"),
                    "page_url": finding.get("page_url"),
                    "page_title": finding.get("page_title"),
                    "selector": finding.get("selector"),
                    "reviewer": info["reviewer"],
                    "reviewer_notes": info["notes"]
                })
                new_passed_count += 1
            elif verdict == "n-a":
                pass
            else:
                new_manual_reviews.append(finding)

        audit_data["manual_reviews"] = new_manual_reviews
        audit_data["violations"] = violations
        audit_data["passed"] = passed

        audit_data["total_manual_reviews"] = len(new_manual_reviews)
        audit_data["total_violations"] = len(violations)
        audit_data["total_passed"] = len(passed)

        # Re-generate violation counts
        violation_types = {}
        for f in violations:
            r = f.get("rule")
            if r:
                violation_types[r] = violation_types.get(r, 0) + 1
        audit_data["violation_types"] = violation_types

        manual_review_types = {}
        for f in new_manual_reviews:
            r = f.get("rule")
            if r:
                manual_review_types[r] = manual_review_types.get(r, 0) + 1
        audit_data["manual_review_types"] = manual_review_types

        target_out = output or audit_json
        Path(target_out).write_text(json.dumps(audit_data, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Successfully merged verdicts: {new_violations_count} failures added, {new_passed_count} passes added. Saved to {target_out}.[/green]")

    except Exception as e:
        console.print(f"[red]Error merging reviews: {e}[/red]")
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
