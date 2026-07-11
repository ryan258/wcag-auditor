import json
import csv
import hashlib
import importlib
import tomllib
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from wcag_auditor.auditor import Auditor
from wcag_auditor.cli import cli
from wcag_auditor.reporter import Reporter, WCAG_22_AA_CRITERIA
from wcag_auditor.rules import RuleMetadata

cli_module = importlib.import_module("wcag_auditor.cli")


def test_wcag_22_aa_criteria_are_current_and_have_correct_levels():
    """The generated VPAT and coverage matrix share this normative source."""
    assert len(WCAG_22_AA_CRITERIA) == 55
    assert "4.1.1" not in WCAG_22_AA_CRITERIA
    assert WCAG_22_AA_CRITERIA["3.2.6"]["level"] == "A"
    assert WCAG_22_AA_CRITERIA["3.3.8"]["level"] == "AA"


def test_vpat_does_not_claim_support_without_successful_rule_evidence():
    results = {
        "base_url": "https://example.com",
        "violations": [],
        "manual_reviews": [],
        "passed": [],
        "warnings": [],
    }

    vpat = Reporter(results).generate("vpat")

    assert (
        "1.1.1 Non-text Content (Level A) | Not Evaluated | "
        "No successful automated check was recorded."
    ) in vpat


def test_vpat_does_not_claim_support_when_a_covering_rule_crashed():
    results = {
        "base_url": "https://example.com",
        "violations": [],
        "manual_reviews": [],
        "passed": [{"rule": "complex-alt-text", "wcag": "1.1.1"}],
        "warnings": [{"rule": "complex-alt-text", "message": "Rule evaluation crashed"}],
    }

    vpat = Reporter(results).generate("vpat")

    assert (
        "1.1.1 Non-text Content (Level A) | Not Evaluated | "
        "No successful automated check was recorded."
    ) in vpat

def test_should_visit_includes_excludes():
    auditor = Auditor(
        base_url="https://example.com",
        includes=[r"/blog/", r"/about"],
        excludes=[r"/wp-admin/"],
        respect_robots=False
    )
    # Match includes
    assert auditor._should_visit("https://example.com/blog/post-1") is True
    assert auditor._should_visit("https://example.com/about") is True
    # Non-matching includes
    assert auditor._should_visit("https://example.com/contact") is False
    # Matching excludes
    assert auditor._should_visit("https://example.com/blog/wp-admin/login") is False

@patch("urllib.robotparser.RobotFileParser")
def test_should_visit_respects_robots(mock_parser_class):
    mock_parser = mock_parser_class.return_value
    mock_parser.can_fetch.return_value = False

    auditor = Auditor(
        base_url="https://example.com",
        respect_robots=True
    )
    auditor.robots_parser = mock_parser
    auditor.robots_loaded = True

    # Blocked by robots
    assert auditor._should_visit("https://example.com/secret") is False
    mock_parser.can_fetch.assert_called_with(auditor.user_agent, "https://example.com/secret")


def test_should_visit_allows_discovered_urls_when_robots_could_not_be_loaded():
    auditor = Auditor(base_url="https://example.com", respect_robots=True)

    # An unread RobotFileParser rejects all URLs. A failed robots.txt request
    # must not silently reduce a crawl to its seed page.
    assert auditor._should_visit("https://example.com/next") is True

@patch("wcag_auditor.auditor.sync_playwright")
def test_auditor_storage_state_and_delay(mock_sync_playwright):
    mock_playwright = mock_sync_playwright.return_value.__enter__.return_value
    mock_browser = mock_playwright.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value

    with patch("wcag_auditor.auditor.Auditor._extract_links", return_value=[]), \
         patch("wcag_auditor.auditor.Auditor._check_page") as mock_check_page:

        mock_result = MagicMock()
        mock_result.violations = []
        mock_result.warnings = []
        mock_result.passed = []
        mock_result.manual_reviews = []
        mock_result.page_title = "Home"
        mock_result.page_insights = {"template": "home", "page_type": "home", "url": "https://example.com"}
        mock_check_page.return_value = mock_result

        auditor = Auditor(
            base_url="https://example.com",
            storage_state="state.json",
            delay=100
        )
        auditor.audit()

        # Verify storage state passed to context
        mock_browser.new_context.assert_called_once_with(
            user_agent=auditor.user_agent,
            storage_state="state.json"
        )

def test_vpat_generation():
    results = {
        "base_url": "https://example.com",
        "violations": [
            {
                "rule": "empty-links",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "message": "Link has no text",
                "page_url": "https://example.com/about"
            }
        ],
        "manual_reviews": [
            {
                "rule": "focus-not-obscured",
                "wcag": "2.4.11",
                "level": "AA",
                "impact": "serious",
                "message": "Sticky header obscures focus",
                "page_url": "https://example.com/contact"
            }
        ],
        "passed": [{"rule": "complex-alt-text", "wcag": "1.1.1"}]
    }

    reporter = Reporter(results)
    vpat = reporter.generate("vpat")

    # 2.4.4 is partially supported
    assert "2.4.4 Link Purpose (In Context) (Level A) | Partially Supports | Issues found: Link has no text" in vpat
    # 2.4.11 is Not Evaluated
    assert "2.4.11 Focus Not Obscured (Minimum) (Level AA) | Not Evaluated | Requires manual review" in vpat
    # Unsupported or covered rules without violations are Supports
    assert "1.1.1 Non-text Content (Level A) | Supports | Supports (automated checks only)" in vpat
    # Uncovered rules are Not Evaluated (Requires manual assessment)
    assert "1.4.1 Use of Color (Level A) | Not Evaluated | Requires manual assessment" in vpat

def test_sarif_generation():
    results = {
        "base_url": "https://example.com",
        "violations": [
            {
                "rule": "empty-links",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "message": "Link has no text",
                "page_url": "https://example.com/about",
                "element": "<a>"
            }
        ],
        "manual_reviews": []
    }

    reporter = Reporter(results)
    sarif = json.loads(reporter.generate("sarif"))

    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "WCAG Auditor"
    assert len(run["results"]) == 1
    res = run["results"][0]
    assert res["ruleId"] == "empty-links"
    assert res["level"] == "error"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "https://example.com/about"


@patch("wcag_auditor.cli.Progress")
@patch("wcag_auditor.cli.Auditor")
def test_audit_progress_uses_the_stderr_console(mock_auditor_class, mock_progress):
    mock_progress.return_value.__enter__.return_value.add_task.return_value = "audit"
    mock_auditor_class.return_value.audit.return_value = {
        "base_url": "https://example.com",
        "violations": [],
        "manual_reviews": [],
        "passed": [],
        "warnings": [],
    }

    result = CliRunner().invoke(cli, ["audit", "https://example.com", "--format", "json"])

    assert result.exit_code == 0
    assert mock_progress.call_args.kwargs["console"] is cli_module.console


def test_declared_playwright_minimum_supports_aria_snapshots():
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "playwright>=1.49.0" in project["project"]["dependencies"]


def test_check_page_enriches_a_unique_static_html_finding(page):
    page.set_content('<html><head><title>Example</title></head><body><button id="save">Save</button></body></html>')
    rule = MagicMock()
    rule.metadata = RuleMetadata(
        id="static-snippet",
        description="Static snippet rule",
        wcag_criterion="4.1.2",
        level="A",
        impact="serious",
        applicability="button",
    )
    rule.evaluate.return_value = [{
        "element": '<button id="save">Save</button>',
        "message": "Example finding",
        "suggestion": "Fix it",
    }]
    auditor = Auditor(base_url="https://example.com", respect_robots=False)
    auditor.wcag_rules = [rule]

    with patch.object(
        auditor,
        "_collect_page_insights",
        return_value={"template": "/", "page_type": "home"},
    ):
        result = auditor._check_page(page, "https://example.com/")

    finding = result.violations[0]
    assert finding["page_url"] == "https://example.com/"
    assert finding["page_title"] == "Example"
    assert finding["selector"] == "#save"
    assert finding["accessible_name"] == "Save"

@patch("wcag_auditor.cli.Auditor")
def test_cli_baseline_suppression(mock_auditor_class, tmp_path):
    mock_auditor = mock_auditor_class.return_value
    mock_auditor.audit.return_value = {
        "base_url": "https://example.com",
        "violations": [
            {
                "rule": "empty-links",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "message": "Link has no text",
                "page_url": "https://example.com/",
                "page_template": "/",
                "selector": "#bad-link"
            },
            {
                "rule": "empty-links",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "message": "Another link has no text",
                "page_url": "https://example.com/about",
                "page_template": "/about",
                "selector": "#another-bad-link"
            }
        ],
        "manual_reviews": [],
        "passed": [],
        "warnings": []
    }

    # Create baseline file with first violation suppressed
    key = "empty-links:/:#bad-link"
    fp = hashlib.sha256(key.encode("utf-8")).hexdigest()

    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps([{"fingerprint": fp}]), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, [
        "audit", "https://example.com",
        "--format", "json",
        "--baseline", str(baseline_file)
    ])

    assert result.exit_code == 0
    json_start = result.output.find("{")
    report = json.loads(result.output[json_start:] if json_start != -1 else result.output)

    # 1 active violation, 1 suppressed known issue
    assert report["summary"]["total_violations"] == 1
    assert len(report["violations"]) == 1
    assert report["violations"][0]["selector"] == "#another-bad-link"
    assert len(report["known_issues"]) == 1
    assert report["known_issues"][0]["selector"] == "#bad-link"

@patch("wcag_auditor.cli.Auditor")
def test_cli_fail_on_threshold(mock_auditor_class):
    mock_auditor = mock_auditor_class.return_value
    mock_auditor.audit.return_value = {
        "base_url": "https://example.com",
        "violations": [
            {
                "rule": "empty-links",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "message": "Link has no text",
                "page_url": "https://example.com/",
                "page_template": "/",
                "selector": "#bad-link"
            }
        ],
        "manual_reviews": [],
        "passed": [],
        "warnings": []
    }

    runner = CliRunner()

    # Should exit with code 1 because impact is serious >= threshold serious
    result = runner.invoke(cli, ["audit", "https://example.com", "--fail-on", "serious"])
    assert result.exit_code == 1

    # Should not fail (exit 0) because threshold critical > serious
    result2 = runner.invoke(cli, ["audit", "https://example.com", "--fail-on", "critical"])
    assert result2.exit_code == 0

def test_cli_review_export_merge(tmp_path):
    audit_file = tmp_path / "audit.json"
    audit_data = {
        "base_url": "https://example.com",
        "violations": [],
        "manual_reviews": [
            {
                "rule": "focus-not-obscured",
                "wcag": "2.4.11",
                "level": "AA",
                "impact": "serious",
                "message": "Sticky header obscures focus",
                "page_url": "https://example.com/contact",
                "fingerprint": "mock-fp-123",
                "element": "<a>"
            }
        ],
        "passed": []
    }
    audit_file.write_text(json.dumps(audit_data), encoding="utf-8")

    runner = CliRunner()

    # 1. Export CSV
    csv_file = tmp_path / "checklist.csv"
    res_export = runner.invoke(cli, ["review", "export", str(audit_file), "-f", "csv", "-o", str(csv_file)])
    assert res_export.exit_code == 0
    assert csv_file.exists()

    # Update CSV with verdict
    lines = []
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)
        row[5] = "fail"
        row[6] = "TestReviewer"
        row[7] = "Obscured by login banner"

    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(row)

    # 2. Merge
    merged_file = tmp_path / "merged.json"
    res_merge = runner.invoke(cli, ["review", "merge", str(audit_file), str(csv_file), "-o", str(merged_file)])
    assert res_merge.exit_code == 0

    merged_data = json.loads(merged_file.read_text(encoding="utf-8"))
    assert len(merged_data["manual_reviews"]) == 0
    assert len(merged_data["violations"]) == 1
    violation = merged_data["violations"][0]
    assert violation["finding_type"] == "violation"
    assert violation["reviewer"] == "TestReviewer"
    assert violation["reviewer_notes"] == "Obscured by login banner"
