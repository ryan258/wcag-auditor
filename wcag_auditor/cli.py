"""Command-line interface for WCAG Auditor."""
import click
import json
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from wcag_auditor.auditor import Auditor
from wcag_auditor.reporter import Reporter
from wcag_auditor import __version__

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
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "html", "markdown", "text"]), default="text", help="Output format (default: text)")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
@click.option("--user-agent", "-u", default="WCAG-Auditor/0.1.0", help="User agent string for requests")
def audit(url: str, depth: int, max_pages: int, output_format: str, output: Optional[str], timeout: int, user_agent: str):
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
                user_agent=user_agent
            )
            
            results = auditor.audit()
            progress.update(task, description="Generating report...")
            
            reporter = Reporter(results)
            report = reporter.generate(output_format)
            
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
            table = Table(title="WCAG Violations Summary")
            table.add_column("Rule", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            table.add_column("Impact", style="red")
            
            for violation in violations:
                table.add_row(
                    violation.get("rule", "Unknown"),
                    str(violation.get("count", 0)),
                    violation.get("impact", "Unknown")
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
def summary(url: str, depth: int, max_pages: int, timeout: int):
    """Generate a summary report of WCAG compliance."""
    try:
        auditor = Auditor(
            base_url=url,
            max_depth=depth,
            max_pages=max_pages,
            timeout=timeout
        )
        
        results = auditor.audit()
        reporter = Reporter(results)
        
        # Generate summary statistics
        total_pages = results.get("pages_audited", 0)
        total_violations = results.get("total_violations", 0)
        violation_types = results.get("violation_types", {})
        
        console.print(f"\n[bold]WCAG Audit Summary for {url}[/bold]")
        console.print(f"Pages audited: {total_pages}")
        console.print(f"Total violations: {total_violations}")
        
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

def main():
    cli()

if __name__ == "__main__":
    main()