"""Report generation for WCAG audit results."""

import html
import json
from datetime import datetime
from typing import Any, Dict, List

from wcag_auditor import __version__


def _esc(value: Any) -> str:
    """HTML-escape a value for safe interpolation into markup."""
    return html.escape(str(value))


class Reporter:
    """Generate reports from audit results."""

    def __init__(self, results: Dict[str, Any]):
        self.results = results

    def generate(self, format: str) -> str:
        """Generate report in specified format."""
        if format == "json":
            return self._generate_json()
        if format == "html":
            return self._generate_html()
        if format == "markdown":
            return self._generate_markdown()
        if format == "vpat":
            return self._generate_vpat()
        return self._generate_text()

    def _summary(self) -> Dict[str, Any]:
        return {
            "base_url": self.results.get("base_url"),
            "pages_audited": self.results.get("pages_audited", 0),
            "total_violations": self.results.get("total_violations", 0),
            "total_manual_reviews": self.results.get("total_manual_reviews", 0),
            "total_warnings": self.results.get("total_warnings", 0),
            "total_passed": self.results.get("total_passed", 0),
        }

    def _render_markdown_findings(self, findings: List[Dict[str, Any]], heading: str) -> str:
        if not findings:
            return f"## {heading} (0)\n\nNone.\n"

        # Group findings by rule so shared metadata isn't repeated.
        from collections import OrderedDict

        groups: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        for finding in findings:
            rule = finding.get("rule", "Unknown")
            if rule not in groups:
                groups[rule] = {
                    "rule": rule,
                    "wcag": finding.get("wcag", "Unknown"),
                    "level": finding.get("level", "Unknown"),
                    "impact": finding.get("impact", "Unknown"),
                    "description": finding.get("description", "No description"),
                    "suggestion": finding.get("suggestion", "No suggestion"),
                    "remediation_code": finding.get("remediation_code"),
                    "instances": [],
                }
            groups[rule]["instances"].append(finding)

        total = len(findings)
        blocks = [f"## {heading} ({total} across {len(groups)} rules)\n"]
        for group in groups.values():
            instances = group["instances"]
            block = [
                f"### {group['rule']} ({len(instances)})",
                f"- **WCAG:** {group['wcag']} (Level {group['level']})",
                f"- **Impact:** {group['impact']}",
                f"- **Description:** {group['description']}",
                f"- **Suggestion:** {group['suggestion']}",
            ]
            remediation = group.get("remediation_code")
            if remediation:
                block.append("\n```html")
                block.append(remediation)
                block.append("```")

            block.append("")
            block.append("| # | Element | Message |")
            block.append("|---|---------|---------|")
            for idx, instance in enumerate(instances, 1):
                element = str(instance.get("element", "Unknown")).replace("|", "\\|").replace("\n", " ")
                message = str(instance.get("message", "")).replace("|", "\\|").replace("\n", " ")
                block.append(f"| {idx} | `{element}` | {message} |")

            blocks.append("\n".join(block))
            blocks.append("")
        return "\n".join(blocks)

    def _render_text_findings(self, findings: List[Dict[str, Any]], heading: str) -> str:
        lines = [f"{heading.upper()} ({len(findings)})", "-" * (len(heading) + 4), ""]
        if not findings:
            lines.append("None.")
            lines.append("")
            return "\n".join(lines)

        for finding in findings:
            lines.append(f"Rule: {finding.get('rule', 'Unknown')}")
            if finding.get("wcag") or finding.get("level"):
                wcag = finding.get("wcag", "Unknown")
                level = finding.get("level", "Unknown")
                lines.append(f"WCAG: {wcag} (Level {level})")
            if finding.get("impact"):
                lines.append(f"Impact: {finding['impact']}")
            if finding.get("description"):
                lines.append(f"Description: {finding['description']}")
            lines.append(f"Element: {finding.get('element', 'Unknown')}")
            lines.append(f"Message: {finding.get('message', 'No message')}")
            if finding.get("suggestion"):
                lines.append(f"Suggestion: {finding['suggestion']}")
            remediation = finding.get("remediation_code")
            if remediation:
                lines.append("Remediation:")
                lines.append(remediation)
            lines.append("")
        return "\n".join(lines)

    def _render_text_messages(self, items: List[Dict[str, Any]], heading: str) -> str:
        lines = [f"{heading.upper()} ({len(items)})", "-" * (len(heading) + 4), ""]
        if not items:
            lines.append("None.")
            lines.append("")
            return "\n".join(lines)

        for item in items:
            lines.append(f"Rule: {item.get('rule', 'Unknown')}")
            lines.append(f"Message: {item.get('message', 'No message')}")
            lines.append("")
        return "\n".join(lines)

    def _render_text_passed_checks(self, items: List[Dict[str, Any]]) -> str:
        lines = [f"PASSED CHECKS ({len(items)})", "-----------------", ""]
        if not items:
            lines.append("None.")
            lines.append("")
            return "\n".join(lines)

        for item in items:
            lines.append(f"Rule: {item.get('rule', 'Unknown')}")
            lines.append(f"Description: {item.get('description', 'No description')}")
            lines.append(f"WCAG: {item.get('wcag', 'Unknown')} (Level {item.get('level', 'Unknown')})")
            lines.append("")
        return "\n".join(lines)

    def _render_markdown_user_pass(self) -> str:
        user_pass = self.results.get("user_pass")
        if not user_pass:
            return ""

        lines = [
            "## Synthetic User Pass",
            "",
            "- **Status:** {0}".format(user_pass.get("status", "unknown")),
            "- **Provider:** {0}".format(user_pass.get("provider", "unknown")),
            "- **Pages reviewed:** {0}".format(user_pass.get("pages_reviewed", 0)),
        ]

        agents = user_pass.get("agents", [])
        if agents:
            lines.append("- **Models:** {0}".format(", ".join(
                "{0}={1}".format(agent.get("agent_id", "unknown"), agent.get("model", "unknown"))
                for agent in agents
            )))

        limitations = user_pass.get("limitations", [])
        if limitations:
            lines.extend(["", "### Limits", ""])
            for limitation in limitations:
                lines.append("- {0}".format(limitation))

        errors = user_pass.get("errors", [])
        if errors:
            lines.extend(["", "### Errors", ""])
            for error in errors:
                lines.append("- **{0}:** {1}".format(error.get("stage", "stage"), error.get("message", "Unknown error")))

        themes = user_pass.get("themes", [])
        lines.extend(["", "### Themes ({0})".format(len(themes)), ""])
        if themes:
            for theme in themes:
                lines.append("#### {0} on {1}".format(
                    theme.get("category", "general"),
                    theme.get("page_title") or theme.get("page_url", "Unknown page"),
                ))
                lines.append("- **Target:** {0}".format(theme.get("target_text", "General page flow")))
                lines.append("- **Issue:** {0}".format(theme.get("issue", "No issue provided")))
                lines.append("- **Suggested change:** {0}".format(theme.get("suggested_change", "No suggestion provided")))
                lines.append("- **Agents:** {0}".format(", ".join(theme.get("agent_ids", [])) or "None"))
                lines.append("")
        else:
            lines.append("None.")

        rewrites = user_pass.get("rewrite_suggestions", [])
        lines.extend(["", "### Rewrite Suggestions ({0})".format(len(rewrites)), ""])
        if rewrites:
            for rewrite in rewrites:
                lines.append("- **Page:** {0}".format(rewrite.get("page_url", "Unknown")))
                lines.append("  **Location:** {0}".format(rewrite.get("location", "General copy")))
                lines.append("  **Current:** `{0}`".format(rewrite.get("current_text", "")))
                lines.append("  **Proposed:** `{0}`".format(rewrite.get("proposed_text", "")))
                lines.append("  **Why:** {0}".format(rewrite.get("rationale", "No rationale provided")))
        else:
            lines.append("None.")

        lines.append("")
        return "\n".join(lines)

    def _render_text_user_pass(self) -> str:
        user_pass = self.results.get("user_pass")
        if not user_pass:
            return ""

        lines = [
            "SYNTHETIC USER PASS",
            "-------------------",
            "",
            "Status: {0}".format(user_pass.get("status", "unknown")),
            "Provider: {0}".format(user_pass.get("provider", "unknown")),
            "Pages reviewed: {0}".format(user_pass.get("pages_reviewed", 0)),
            "",
        ]

        agents = user_pass.get("agents", [])
        if agents:
            lines.append("Models: {0}".format(", ".join(
                "{0}={1}".format(agent.get("agent_id", "unknown"), agent.get("model", "unknown"))
                for agent in agents
            )))
            lines.append("")

        for limitation in user_pass.get("limitations", []):
            lines.append("Limit: {0}".format(limitation))
        if user_pass.get("limitations"):
            lines.append("")

        for error in user_pass.get("errors", []):
            lines.append("Error ({0}): {1}".format(error.get("stage", "stage"), error.get("message", "Unknown error")))
        if user_pass.get("errors"):
            lines.append("")

        themes_header = "Themes ({0})".format(len(user_pass.get("themes", [])))
        lines.append(themes_header)
        lines.append("-" * len(themes_header))
        lines.append("")
        for theme in user_pass.get("themes", []):
            lines.append("Category: {0}".format(theme.get("category", "general")))
            lines.append("Page: {0}".format(theme.get("page_title") or theme.get("page_url", "Unknown page")))
            lines.append("Target: {0}".format(theme.get("target_text", "General page flow")))
            lines.append("Issue: {0}".format(theme.get("issue", "No issue provided")))
            lines.append("Suggested change: {0}".format(theme.get("suggested_change", "No suggestion provided")))
            lines.append("Agents: {0}".format(", ".join(theme.get("agent_ids", [])) or "None"))
            lines.append("")
        if not user_pass.get("themes"):
            lines.append("None.")
            lines.append("")

        rewrites_header = "Rewrite Suggestions ({0})".format(len(user_pass.get("rewrite_suggestions", [])))
        lines.append(rewrites_header)
        lines.append("-" * len(rewrites_header))
        lines.append("")
        for rewrite in user_pass.get("rewrite_suggestions", []):
            lines.append("Page: {0}".format(rewrite.get("page_url", "Unknown")))
            lines.append("Location: {0}".format(rewrite.get("location", "General copy")))
            lines.append("Current: {0}".format(rewrite.get("current_text", "")))
            lines.append("Proposed: {0}".format(rewrite.get("proposed_text", "")))
            lines.append("Why: {0}".format(rewrite.get("rationale", "No rationale provided")))
            lines.append("")
        if not user_pass.get("rewrite_suggestions"):
            lines.append("None.")
            lines.append("")

        return "\n".join(lines)

    def _render_html_user_pass(self) -> str:
        user_pass = self.results.get("user_pass")
        if not user_pass:
            return ""

        html_output = """
    <div class="user-pass">
        <h2>Synthetic User Pass</h2>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Pages reviewed:</strong> {pages_reviewed}</p>
""".format(
            status=_esc(user_pass.get("status", "unknown")),
            provider=_esc(user_pass.get("provider", "unknown")),
            pages_reviewed=_esc(user_pass.get("pages_reviewed", 0)),
        )

        agents = user_pass.get("agents", [])
        if agents:
            html_output += """
        <p><strong>Models:</strong> {models}</p>
""".format(
                models=_esc(", ".join(
                    "{0}={1}".format(agent.get("agent_id", "unknown"), agent.get("model", "unknown"))
                    for agent in agents
                ))
            )

        if user_pass.get("limitations"):
            html_output += "        <h3>Limits</h3>\n        <ul>\n"
            for limitation in user_pass.get("limitations", []):
                html_output += "            <li>{0}</li>\n".format(_esc(limitation))
            html_output += "        </ul>\n"

        if user_pass.get("errors"):
            html_output += "        <h3>Errors</h3>\n"
            for error in user_pass.get("errors", []):
                html_output += """
        <div class="warning">
            <div class="rule">{stage}</div>
            <p>{message}</p>
        </div>
""".format(
                    stage=_esc(error.get("stage", "stage")),
                    message=_esc(error.get("message", "Unknown error")),
                )

        html_output += "        <h3>Themes ({0})</h3>\n".format(len(user_pass.get("themes", [])))
        if user_pass.get("themes"):
            for theme in user_pass.get("themes", []):
                html_output += """
        <div class="user-pass-theme">
            <div class="rule">{category}</div>
            <p><strong>Page:</strong> {page}</p>
            <p><strong>Target:</strong> {target}</p>
            <p><strong>Issue:</strong> {issue}</p>
            <p><strong>Suggested change:</strong> {suggested_change}</p>
            <p><strong>Agents:</strong> {agents}</p>
        </div>
""".format(
                    category=_esc(theme.get("category", "general")),
                    page=_esc(theme.get("page_title") or theme.get("page_url", "Unknown page")),
                    target=_esc(theme.get("target_text", "General page flow")),
                    issue=_esc(theme.get("issue", "No issue provided")),
                    suggested_change=_esc(theme.get("suggested_change", "No suggestion provided")),
                    agents=_esc(", ".join(theme.get("agent_ids", [])) or "None"),
                )
        else:
            html_output += "        <p>None.</p>\n"

        html_output += "        <h3>Rewrite Suggestions ({0})</h3>\n".format(len(user_pass.get("rewrite_suggestions", [])))
        if user_pass.get("rewrite_suggestions"):
            for rewrite in user_pass.get("rewrite_suggestions", []):
                html_output += """
        <div class="user-pass-rewrite">
            <p><strong>Page:</strong> {page}</p>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Current:</strong> <code>{current_text}</code></p>
            <p><strong>Proposed:</strong> <code>{proposed_text}</code></p>
            <p><strong>Why:</strong> {rationale}</p>
        </div>
""".format(
                    page=_esc(rewrite.get("page_url", "Unknown")),
                    location=_esc(rewrite.get("location", "General copy")),
                    current_text=_esc(rewrite.get("current_text", "")),
                    proposed_text=_esc(rewrite.get("proposed_text", "")),
                    rationale=_esc(rewrite.get("rationale", "No rationale provided")),
                )
        else:
            html_output += "        <p>None.</p>\n"

        html_output += "    </div>\n"
        return html_output

    def _generate_json(self) -> str:
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "WCAG Auditor",
                "version": __version__,
            },
            "summary": self._summary(),
            "violation_types": self.results.get("violation_types", {}),
            "manual_review_types": self.results.get("manual_review_types", {}),
            "violations": self.results.get("violations", []),
            "manual_reviews": self.results.get("manual_reviews", []),
            "warnings": self.results.get("warnings", []),
            "passed": self.results.get("passed", []),
            "pages": self.results.get("pages", []),
            "page_artifacts": self.results.get("page_artifacts", []),
            "sampling": self.results.get("sampling", {}),
            "wcag_em": self.results.get("wcag_em", {}),
            "user_pass": self.results.get("user_pass", {}),
        }
        return json.dumps(report_data, indent=2)

    def _generate_html(self) -> str:
        violations = self.results.get("violations", [])
        manual_reviews = self.results.get("manual_reviews", [])
        warnings = self.results.get("warnings", [])
        passed = self.results.get("passed", [])
        sampling = self.results.get("sampling", {})
        wcag_em = self.results.get("wcag_em", {})
        summary = self._summary()

        html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WCAG Audit Report - {_esc(summary.get('base_url', 'Unknown'))}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }}
        code, pre {{ font-family: Menlo, Monaco, monospace; }}
        .summary, .sampling {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .violation {{ border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; background: #ffebee; }}
        .manual-review {{ border-left: 4px solid #6a1b9a; padding: 10px; margin: 10px 0; background: #f3e5f5; }}
        .warning {{ border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; background: #fff3e0; }}
        .passed {{ border-left: 4px solid #4caf50; padding: 10px; margin: 10px 0; background: #e8f5e8; }}
        .user-pass {{ background: #eef4ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .user-pass-theme, .user-pass-rewrite {{ border-left: 4px solid #1d4ed8; padding: 10px; margin: 10px 0; background: #f8fbff; }}
        .rule {{ font-weight: bold; }}
        .impact {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
        .impact-critical {{ background: #d32f2f; color: white; }}
        .impact-serious {{ background: #ff9800; color: white; }}
        .impact-moderate {{ background: #ffeb3b; color: black; }}
        .impact-minor {{ background: #9e9e9e; color: white; }}
        .impact-unknown {{ background: #607d8b; color: white; }}
    </style>
</head>
<body>
    <h1>WCAG Audit Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>URL:</strong> {_esc(summary.get('base_url', 'Unknown'))}</p>
        <p><strong>Pages Audited:</strong> {summary.get('pages_audited', 0)}</p>
        <p><strong>Total Violations:</strong> {summary.get('total_violations', 0)}</p>
        <p><strong>Needs Manual Review:</strong> {summary.get('total_manual_reviews', 0)}</p>
        <p><strong>Total Warnings:</strong> {summary.get('total_warnings', 0)}</p>
        <p><strong>Total Passed:</strong> {summary.get('total_passed', 0)}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="sampling">
        <h2>WCAG-EM Sampling</h2>
        <p><strong>Strategy:</strong> {_esc(sampling.get('strategy', 'Unknown'))}</p>
        <p><strong>Sampled Pages:</strong> {_esc(sampling.get('sampled_pages', 0))}</p>
        <p><strong>Unique Templates:</strong> {_esc(sampling.get('unique_templates', 0))}</p>
        <p><strong>Methodology:</strong> {_esc(wcag_em.get('methodology', 'Not provided'))}</p>
    </div>
    <h2>Violations ({len(violations)})</h2>
"""

        for finding in violations:
            impact = _esc(finding.get("impact", "unknown"))
            html_output += f"""
    <div class="violation">
        <div class="rule">{_esc(finding.get('rule', 'Unknown'))} <span class="impact impact-{impact}">{impact.upper()}</span></div>
        <p><strong>Description:</strong> {_esc(finding.get('description', 'No description'))}</p>
        <p><strong>WCAG:</strong> {_esc(finding.get('wcag', 'Unknown'))} (Level {_esc(finding.get('level', 'Unknown'))})</p>
        <p><strong>Element:</strong> <code>{_esc(finding.get('element', 'Unknown'))}</code></p>
        <p><strong>Message:</strong> {_esc(finding.get('message', 'No message'))}</p>
        <p><strong>Suggestion:</strong> {_esc(finding.get('suggestion', 'No suggestion'))}</p>
"""
            if finding.get("remediation_code"):
                html_output += f"""        <pre>{_esc(finding.get('remediation_code'))}</pre>
"""
            html_output += "    </div>\n"

        html_output += f"""
    <h2>Needs Manual Review ({len(manual_reviews)})</h2>
"""
        for finding in manual_reviews:
            html_output += f"""
    <div class="manual-review">
        <div class="rule">{_esc(finding.get('rule', 'Unknown'))}</div>
        <p><strong>Description:</strong> {_esc(finding.get('description', 'No description'))}</p>
        <p><strong>WCAG:</strong> {_esc(finding.get('wcag', 'Unknown'))} (Level {_esc(finding.get('level', 'Unknown'))})</p>
        <p><strong>Element:</strong> <code>{_esc(finding.get('element', 'Unknown'))}</code></p>
        <p><strong>Message:</strong> {_esc(finding.get('message', 'No message'))}</p>
        <p><strong>Suggestion:</strong> {_esc(finding.get('suggestion', 'No suggestion'))}</p>
    </div>
"""

        html_output += f"""
    <h2>Warnings ({len(warnings)})</h2>
"""
        for warning in warnings:
            html_output += f"""
    <div class="warning">
        <div class="rule">{_esc(warning.get('rule', 'Unknown'))}</div>
        <p><strong>Message:</strong> {_esc(warning.get('message', 'No message'))}</p>
    </div>
"""

        html_output += self._render_html_user_pass()

        html_output += f"""
    <h2>Passed Checks ({len(passed)})</h2>
"""
        for passed_item in passed:
            html_output += f"""
    <div class="passed">
        <div class="rule">{_esc(passed_item.get('rule', 'Unknown'))}</div>
        <p><strong>Description:</strong> {_esc(passed_item.get('description', 'No description'))} - WCAG {_esc(passed_item.get('wcag', 'Unknown'))} (Level {_esc(passed_item.get('level', 'Unknown'))})</p>
    </div>
"""

        html_output += "</body>\n</html>"
        return html_output

    def _generate_markdown(self) -> str:
        summary = self._summary()
        sampling = self.results.get("sampling", {})
        wcag_em = self.results.get("wcag_em", {})

        report = f"""# WCAG Audit Report

## Summary

- **URL:** {summary.get('base_url', 'Unknown')}
- **Pages Audited:** {summary.get('pages_audited', 0)}
- **Total Violations:** {summary.get('total_violations', 0)}
- **Needs Manual Review:** {summary.get('total_manual_reviews', 0)}
- **Total Warnings:** {summary.get('total_warnings', 0)}
- **Total Passed:** {summary.get('total_passed', 0)}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## WCAG-EM Evaluation Summary

- **Sampling strategy:** {sampling.get('strategy', 'Unknown')}
- **Sampled pages:** {sampling.get('sampled_pages', 0)}
- **Unique templates:** {sampling.get('unique_templates', 0)}
- **Methodology:** {wcag_em.get('methodology', 'Not provided')}

### Representative Pages

"""

        for sample in wcag_em.get("sample", []):
            report += f"- **{sample.get('page_type', 'content')}:** {sample.get('url', 'Unknown')} ({sample.get('template', 'Unknown')})\n"

        report += "\n"
        report += self._render_markdown_findings(self.results.get("violations", []), "Violations")
        report += "\n"
        report += self._render_markdown_findings(self.results.get("manual_reviews", []), "Needs Manual Review")
        report += "\n## Warnings ({})\n\n".format(len(self.results.get("warnings", [])))
        if self.results.get("warnings"):
            for warning in self.results.get("warnings", []):
                report += f"- **{warning.get('rule', 'Unknown')}:** {warning.get('message', 'No message')}\n"
        else:
            report += "None.\n"

        report += "\n"
        report += self._render_markdown_user_pass()
        report += "\n## Passed Checks ({})\n\n".format(len(self.results.get("passed", [])))
        for passed_item in self.results.get("passed", []):
            report += (
                f"- **{passed_item.get('rule', 'Unknown')}:** {passed_item.get('description', 'No description')} "
                f"(WCAG {passed_item.get('wcag', 'Unknown')})\n"
            )

        return report

    def _generate_text(self) -> str:
        summary = self._summary()
        sampling = self.results.get("sampling", {})
        wcag_em = self.results.get("wcag_em", {})

        report = f"""WCAG AUDIT REPORT
==================

URL: {summary.get('base_url', 'Unknown')}
Pages Audited: {summary.get('pages_audited', 0)}
Total Violations: {summary.get('total_violations', 0)}
Needs Manual Review: {summary.get('total_manual_reviews', 0)}
Total Warnings: {summary.get('total_warnings', 0)}
Total Passed: {summary.get('total_passed', 0)}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

WCAG-EM SAMPLING
----------------

Strategy: {sampling.get('strategy', 'Unknown')}
Sampled Pages: {sampling.get('sampled_pages', 0)}
Unique Templates: {sampling.get('unique_templates', 0)}
Methodology: {wcag_em.get('methodology', 'Not provided')}

"""
        if wcag_em.get("sample"):
            report += "Representative Pages:\n"
            for sample in wcag_em.get("sample", []):
                report += f"- {sample.get('page_type', 'content')}: {sample.get('url', 'Unknown')} ({sample.get('template', 'Unknown')})\n"
            report += "\n"

        report += self._render_text_findings(self.results.get("violations", []), "Violations")
        report += "\n"
        report += self._render_text_findings(self.results.get("manual_reviews", []), "Needs Manual Review")
        report += "\n"
        report += self._render_text_messages(self.results.get("warnings", []), "Warnings")
        report += "\n"
        report += self._render_text_user_pass()
        report += "\n"
        report += self._render_text_passed_checks(self.results.get("passed", []))
        return report

    def _generate_vpat(self) -> str:
        violations = self.results.get("violations", [])
        manual_reviews = self.results.get("manual_reviews", [])
        criterions: Dict[str, List[Dict[str, Any]]] = {}

        for finding in violations + manual_reviews:
            criterions.setdefault(finding.get("wcag", "Unknown"), []).append(finding)

        report = f"""# Accessibility Conformance Report (VPAT® Version 2.5)

* **Name of Product/Version:** Automated WCAG Scan
* **Report Date:** {datetime.now().strftime('%Y-%m-%d')}
* **Target:** {self.results.get('base_url', 'Unknown')}
* **Evaluation Methods Used:** Playwright automated testing with representative sampling (`wcag-auditor` version {__version__})

## Applicable Standards/Guidelines

This report covers the degree of conformance for the following accessibility standard/guidelines:
- Web Content Accessibility Guidelines 2.2 Level A and AA

## Terminology

* **Supports:** The functionality of the product has at least one method that meets the criterion without known defects, or meets with equivalent facilitation.
* **Partially Supports:** Some functionality of the product does not meet the criterion.
* **Does Not Support:** The majority of product functionality does not meet the criterion.
* **Not Applicable:** The criterion is not relevant to the product.

## Table 1: Success Criteria, Level A & AA

| Criteria | Conformance Level | Remarks and Explanations |
| --- | --- | --- |
"""

        for wcag, findings in sorted(criterions.items()):
            messages = list(dict.fromkeys(finding.get("message", "") for finding in findings))
            review_note = " Includes needs-review items." if any(
                finding.get("finding_type") == "needs_review" for finding in findings
            ) else ""
            report += f"| {wcag} | Partially Supports | Issues found: {'; '.join(messages)}.{review_note} |\n"

        if not criterions:
            report += "| Overall | Supports | No violations detected in automated scans |\n"

        return report
