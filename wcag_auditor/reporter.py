"""Report generation for WCAG audit results."""

import html
import json
from datetime import datetime
from typing import Any, Dict, List

from wcag_auditor import __version__

WCAG_22_AA_CRITERIA = {
    # 1. Perceivable
    "1.1.1": {"name": "Non-text Content", "level": "A"},
    "1.2.1": {"name": "Audio-only and Video-only (Prerecorded)", "level": "A"},
    "1.2.2": {"name": "Captions (Prerecorded)", "level": "A"},
    "1.2.3": {"name": "Audio Description or Media Alternative (Prerecorded)", "level": "A"},
    "1.2.4": {"name": "Captions (Live)", "level": "AA"},
    "1.2.5": {"name": "Audio Description (Prerecorded)", "level": "AA"},
    "1.3.1": {"name": "Info and Relationships", "level": "A"},
    "1.3.2": {"name": "Meaningful Sequence", "level": "A"},
    "1.3.3": {"name": "Sensory Characteristics", "level": "A"},
    "1.3.4": {"name": "Orientation", "level": "AA"},
    "1.3.5": {"name": "Identify Input Purpose", "level": "AA"},
    "1.4.1": {"name": "Use of Color", "level": "A"},
    "1.4.2": {"name": "Audio Control", "level": "A"},
    "1.4.3": {"name": "Contrast (Minimum)", "level": "AA"},
    "1.4.4": {"name": "Resize Text", "level": "AA"},
    "1.4.5": {"name": "Images of Text", "level": "AA"},
    "1.4.10": {"name": "Reflow", "level": "AA"},
    "1.4.11": {"name": "Non-text Contrast", "level": "AA"},
    "1.4.12": {"name": "Text Spacing", "level": "AA"},
    "1.4.13": {"name": "Content on Hover or Focus", "level": "AA"},
    # 2. Operable
    "2.1.1": {"name": "Keyboard", "level": "A"},
    "2.1.2": {"name": "No Keyboard Trap", "level": "A"},
    "2.1.4": {"name": "Character Key Shortcuts", "level": "A"},
    "2.2.1": {"name": "Timing Adjustable", "level": "A"},
    "2.2.2": {"name": "Pause, Stop, Hide", "level": "A"},
    "2.3.1": {"name": "Three Flashes or Below Threshold", "level": "A"},
    "2.4.1": {"name": "Bypass Blocks", "level": "A"},
    "2.4.2": {"name": "Page Titled", "level": "A"},
    "2.4.3": {"name": "Focus Order", "level": "A"},
    "2.4.4": {"name": "Link Purpose (In Context)", "level": "A"},
    "2.4.5": {"name": "Multiple Ways", "level": "AA"},
    "2.4.6": {"name": "Headings and Labels", "level": "AA"},
    "2.4.7": {"name": "Focus Visible", "level": "AA"},
    "2.4.11": {"name": "Focus Not Obscured (Minimum)", "level": "AA"},
    "2.5.1": {"name": "Pointer Gestures", "level": "A"},
    "2.5.2": {"name": "Pointer Cancellation", "level": "A"},
    "2.5.3": {"name": "Label in Name", "level": "A"},
    "2.5.4": {"name": "Motion Actuation", "level": "A"},
    "2.5.7": {"name": "Dragging Movements", "level": "AA"},
    "2.5.8": {"name": "Target Size (Minimum)", "level": "AA"},
    # 3. Understandable
    "3.1.1": {"name": "Language of Page", "level": "A"},
    "3.1.2": {"name": "Language of Parts", "level": "AA"},
    "3.2.1": {"name": "On Focus", "level": "A"},
    "3.2.2": {"name": "On Input", "level": "A"},
    "3.2.3": {"name": "Consistent Navigation", "level": "AA"},
    "3.2.4": {"name": "Consistent Identification", "level": "AA"},
    "3.2.6": {"name": "Consistent Help", "level": "A"},
    "3.3.1": {"name": "Error Identification", "level": "A"},
    "3.3.2": {"name": "Labels or Instructions", "level": "A"},
    "3.3.3": {"name": "Error Suggestion", "level": "AA"},
    "3.3.4": {"name": "Error Prevention (Legal, Financial, Data)", "level": "AA"},
    "3.3.7": {"name": "Redundant Entry", "level": "A"},
    "3.3.8": {"name": "Accessible Authentication (Minimum)", "level": "AA"},
    # 4. Robust
    "4.1.2": {"name": "Name, Role, Value", "level": "A"},
    "4.1.3": {"name": "Status Messages", "level": "AA"}
}


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
        if format == "sarif":
            return self._generate_sarif()
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

            # Check if any instance was truncated, and display a note
            is_truncated = any(inst.get("truncated") for inst in instances)
            total_matched = max(inst.get("total", len(instances)) for inst in instances) if is_truncated else len(instances)
            truncation_suffix = f" (showing {len(instances)} of {total_matched})" if is_truncated else ""

            block = [
                f"### {group['rule']} ({len(instances)}){truncation_suffix}",
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
            block.append("| # | Page | Element | Message / Identity |")
            block.append("|---|------|---------|--------------------|")
            for idx, instance in enumerate(instances, 1):
                page_url = instance.get("page_url")
                page_title = instance.get("page_title", "Page")
                page_cell = f"[{page_title}]({page_url})" if page_url else "Unknown"

                element = str(instance.get("element", "Unknown")).replace("|", "\\|").replace("\n", " ")
                message = str(instance.get("message", "")).replace("|", "\\|").replace("\n", " ")

                details = []
                if instance.get("selector"):
                    details.append(f"**Selector:** `{instance['selector']}`")
                if instance.get("accessible_name"):
                    details.append(f"**Name:** \"{instance['accessible_name']}\"")
                if instance.get("role"):
                    details.append(f"**Role:** `{instance['role']}`")
                if instance.get("bounding_box"):
                    bbox = instance["bounding_box"]
                    details.append(f"**Coords:** x={bbox.get('x')}, y={bbox.get('y')}, w={bbox.get('width')}, h={bbox.get('height')}")
                if instance.get("frame_context"):
                    fc = instance["frame_context"]
                    details.append(f"**Frame:** `{fc.get('src') or fc.get('name')}`")

                if details:
                    escaped_details = [d.replace("|", "\\|") for d in details]
                    message += " <br>" + " \\| ".join(escaped_details)

                block.append(f"| {idx} | {page_cell} | `{element}` | {message} |")

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
            "known_issues": self.results.get("known_issues", []),
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
        <p><strong>URL:</strong> <a href="{_esc(summary.get('base_url', 'Unknown'))}">{_esc(summary.get('base_url', 'Unknown'))}</a></p>
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
            page_url = finding.get("page_url", "")
            page_title = finding.get("page_title", "Page")
            page_html = f'<p><strong>Page:</strong> <a href="{_esc(page_url)}">{_esc(page_title)}</a></p>' if page_url else ''

            trunc_badge = ""
            if finding.get("truncated"):
                trunc_badge = f' <span class="impact" style="background: #7986cb; color: white;">TRUNCATED (showing some of {finding.get("total")})</span>'

            html_output += f"""
    <div class="violation">
        <div class="rule">{_esc(finding.get('rule', 'Unknown'))} <span class="impact impact-{impact}">{impact.upper()}</span>{trunc_badge}</div>
        {page_html}
        <p><strong>Description:</strong> {_esc(finding.get('description', 'No description'))}</p>
        <p><strong>WCAG:</strong> {_esc(finding.get('wcag', 'Unknown'))} (Level {_esc(finding.get('level', 'Unknown'))})</p>
        <p><strong>Element:</strong> <code>{_esc(finding.get('element', 'Unknown'))}</code></p>
"""
            if finding.get("selector"):
                html_output += f"        <p><strong>Selector:</strong> <code>{_esc(finding['selector'])}</code></p>\n"
            if finding.get("accessible_name"):
                html_output += f"        <p><strong>Accessible Name:</strong> <code>\"{_esc(finding['accessible_name'])}\"</code></p>\n"
            if finding.get("role"):
                html_output += f"        <p><strong>Role:</strong> <code>{_esc(finding['role'])}</code></p>\n"
            if finding.get("bounding_box"):
                bbox = finding["bounding_box"]
                html_output += f"        <p><strong>Bounding Box:</strong> <code>x={bbox.get('x')}, y={bbox.get('y')}, w={bbox.get('width')}, h={bbox.get('height')}</code></p>\n"
            if finding.get("frame_context"):
                fc = finding["frame_context"]
                html_output += f"        <p><strong>Frame Context:</strong> <code>{_esc(fc)}</code></p>\n"

            html_output += f"""
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
            page_url = finding.get("page_url", "")
            page_title = finding.get("page_title", "Page")
            page_html = f'<p><strong>Page:</strong> <a href="{_esc(page_url)}">{_esc(page_title)}</a></p>' if page_url else ''

            trunc_badge = ""
            if finding.get("truncated"):
                trunc_badge = f' <span class="impact" style="background: #7986cb; color: white;">TRUNCATED (showing some of {finding.get("total")})</span>'

            html_output += f"""
    <div class="manual-review">
        <div class="rule">{_esc(finding.get('rule', 'Unknown'))}{trunc_badge}</div>
        {page_html}
        <p><strong>Description:</strong> {_esc(finding.get('description', 'No description'))}</p>
        <p><strong>WCAG:</strong> {_esc(finding.get('wcag', 'Unknown'))} (Level {_esc(finding.get('level', 'Unknown'))})</p>
        <p><strong>Element:</strong> <code>{_esc(finding.get('element', 'Unknown'))}</code></p>
"""
            if finding.get("selector"):
                html_output += f"        <p><strong>Selector:</strong> <code>{_esc(finding['selector'])}</code></p>\n"
            if finding.get("accessible_name"):
                html_output += f"        <p><strong>Accessible Name:</strong> <code>\"{_esc(finding['accessible_name'])}\"</code></p>\n"
            if finding.get("role"):
                html_output += f"        <p><strong>Role:</strong> <code>{_esc(finding['role'])}</code></p>\n"
            if finding.get("bounding_box"):
                bbox = finding["bounding_box"]
                html_output += f"        <p><strong>Bounding Box:</strong> <code>x={bbox.get('x')}, y={bbox.get('y')}, w={bbox.get('width')}, h={bbox.get('height')}</code></p>\n"
            if finding.get("frame_context"):
                fc = finding["frame_context"]
                html_output += f"        <p><strong>Frame Context:</strong> <code>{_esc(fc)}</code></p>\n"

            html_output += f"""
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
        passed = self.results.get("passed", [])
        warnings = self.results.get("warnings", [])

        from wcag_auditor.rules.core_rules import get_core_rules
        rules = get_core_rules()

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
* **Not Evaluated:** The criterion has not been fully evaluated (needs manual review or requires manual assessment).

## Table 1: Success Criteria, Level A & AA

| Criteria | Conformance Level | Remarks and Explanations |
| --- | --- | --- |
"""
        # Sort criteria by numerical parts
        for wcag, info in sorted(WCAG_22_AA_CRITERIA.items(), key=lambda x: [int(c) for c in x[0].split('.')]):
            # Get findings for this criterion
            crit_violations = [f for f in violations if f.get("wcag") == wcag]
            crit_reviews = [f for f in manual_reviews if f.get("wcag") == wcag]

            # Find rules covering this
            matching_rules = [r for r in rules if r.metadata.wcag_criterion == wcag]
            matching_rule_ids = {rule.metadata.id for rule in matching_rules}
            successful_rule_ids = {
                finding.get("rule")
                for finding in passed
                if finding.get("rule") in matching_rule_ids
            }
            crashed_rule_ids = {
                warning.get("rule")
                for warning in warnings
                if warning.get("rule") in matching_rule_ids
            }

            if crit_violations:
                messages = list(dict.fromkeys(f.get("message", "") for f in crit_violations))
                pages = list(dict.fromkeys(f.get("page_url", "general") for f in crit_violations))
                pages_str = ", ".join(pages)
                report += f"| {wcag} {info['name']} (Level {info['level']}) | Partially Supports | Issues found: {'; '.join(messages)} (on {pages_str}). |\n"
            elif crit_reviews:
                messages = list(dict.fromkeys(f.get("message", "") for f in crit_reviews))
                report += f"| {wcag} {info['name']} (Level {info['level']}) | Not Evaluated | Requires manual review. Findings needing evaluation: {'; '.join(messages)}. |\n"
            elif successful_rule_ids and not crashed_rule_ids:
                report += f"| {wcag} {info['name']} (Level {info['level']}) | Supports | Supports (automated checks only). No violations detected. |\n"
            elif matching_rules:
                report += f"| {wcag} {info['name']} (Level {info['level']}) | Not Evaluated | No successful automated check was recorded. |\n"
            else:
                report += f"| {wcag} {info['name']} (Level {info['level']}) | Not Evaluated | Requires manual assessment (not covered by automated checks). |\n"

        return report

    def _generate_sarif(self) -> str:
        violations = self.results.get("violations", [])
        manual_reviews = self.results.get("manual_reviews", [])

        rules_map = {}
        for rule in violations + manual_reviews:
            rule_id = rule.get("rule", "Unknown")
            if rule_id not in rules_map:
                wcag = rule.get("wcag", "")
                help_url = f"https://www.w3.org/WAI/WCAG22/Understanding/{wcag.replace('.', '-')}.html" if wcag else ""
                rules_map[rule_id] = {
                    "id": rule_id,
                    "name": rule_id,
                    "shortDescription": {
                        "text": rule.get("description", "No description provided")
                    },
                    "helpUri": help_url
                }

        results_list = []
        for finding in violations + manual_reviews:
            rule_id = finding.get("rule", "Unknown")
            is_manual = finding.get("finding_type") == "needs_review"
            message = finding.get("message", "No message")
            if is_manual:
                message = f"[Needs Review] {message}"

            level = "error"
            impact = finding.get("impact", "moderate")
            if impact in ["minor", "moderate"]:
                level = "warning"
            elif impact in ["serious", "critical"]:
                level = "error"

            region = {}
            if finding.get("element"):
                region["snippet"] = {
                    "text": finding["element"]
                }

            result_item = {
                "ruleId": rule_id,
                "message": {
                    "text": message
                },
                "level": level,
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.get("page_url", self.results.get("base_url", ""))
                            },
                            "region": region
                        }
                    }
                ]
            }
            results_list.append(result_item)

        sarif_data = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "WCAG Auditor",
                            "version": __version__,
                            "rules": list(rules_map.values())
                        }
                    },
                    "results": results_list
                }
            ]
        }
        return json.dumps(sarif_data, indent=2)
