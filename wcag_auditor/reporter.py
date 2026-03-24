"""Report generation for WCAG audit results."""
import json
from typing import Dict, Any
from datetime import datetime

class Reporter:
    """Generate reports from audit results."""
    
    def __init__(self, results: Dict[str, Any]):
        self.results = results
    
    def generate(self, format: str) -> str:
        """Generate report in specified format."""
        if format == "json":
            return self._generate_json()
        elif format == "html":
            return self._generate_html()
        elif format == "markdown":
            return self._generate_markdown()
        else:  # text
            return self._generate_text()
    
    def _generate_json(self) -> str:
        """Generate JSON report."""
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "WCAG Auditor",
                "version": "0.1.0"
            },
            "summary": {
                "base_url": self.results.get("base_url"),
                "pages_audited": self.results.get("pages_audited", 0),
                "total_violations": self.results.get("total_violations", 0),
                "total_warnings": self.results.get("total_warnings", 0),
                "total_passed": self.results.get("total_passed", 0)
            },
            "violation_types": self.results.get("violation_types", {}),
            "violations": self.results.get("violations", []),
            "warnings": self.results.get("warnings", []),
            "passed": self.results.get("passed", []),
            "pages": self.results.get("pages", [])
        }
        
        return json.dumps(report_data, indent=2)
    
    def _generate_html(self) -> str:
        """Generate HTML report."""
        violations = self.results.get("violations", [])
        warnings = self.results.get("warnings", [])
        passed = self.results.get("passed", [])
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WCAG Audit Report - {self.results.get('base_url', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .violation {{ border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; background: #ffebee; }}
        .warning {{ border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; background: #fff3e0; }}
        .passed {{ border-left: 4px solid #4caf50; padding: 10px; margin: 10px 0; background: #e8f5e8; }}
        .rule {{ font-weight: bold; }}
        .impact {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
        .impact-critical {{ background: #d32f2f; color: white; }}
        .impact-serious {{ background: #ff9800; color: white; }}
        .impact-moderate {{ background: #ffeb3b; color: black; }}
        .impact-minor {{ background: #9e9e9e; color: white; }}
    </style>
</head>
<body>
    <h1>WCAG Audit Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>URL:</strong> {self.results.get('base_url', 'Unknown')}</p>
        <p><strong>Pages Audited:</strong> {self.results.get('pages_audited', 0)}</p>
        <p><strong>Total Violations:</strong> {self.results.get('total_violations', 0)}</p>
        <p><strong>Total Warnings:</strong> {self.results.get('total_warnings', 0)}</n        <p><strong>Total Passed:</strong> {self.results.get('total_passed', 0)}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>Violations ({len(violations)})</h2>
    """
        
        for violation in violations:
            impact = violation.get('impact', 'unknown')
            html += f"""
    <div class="violation">
        <div class="rule">{violation.get('rule', 'Unknown')} <span class="impact impact-{impact}">{impact.upper()}</span></div>
        <p><strong>Description:</strong> {violation.get('description', 'No description')}</p>
        <p><strong>WCAG:</strong> {violation.get('wcag', 'Unknown')} (Level {violation.get('level', 'Unknown')})</p>
        <p><strong>Element:</strong> <code>{violation.get('element', 'Unknown')}</code></p>
        <p><strong>Message:</strong> {violation.get('message', 'No message')}</p>
        <p><strong>Suggestion:</strong> {violation.get('suggestion', 'No suggestion')}</p>
    </div>
    """
        
        html += f"""
    <h2>Warnings ({len(warnings)})</h2>
    """
        
        for warning in warnings:
            html += f"""
    <div class="warning">
        <div class="rule">{warning.get('rule', 'Unknown')}</div>
        <p><strong>Message:</strong> {warning.get('message', 'No message')}</p>
    </div>
    """
        
        html += f"""
    <h2>Passed Checks ({len(passed)})</h2>
    """
        
        for passed_item in passed:
            html += f"""
    <div class="passed">
        <div class="rule">{passed_item.get('rule', 'Unknown')}</div>
        <p><strong>Description:</ WCAG {passed_item.get('wcag', 'Unknown')} (Level {passed_item.get('level', 'Unknown')})</p>
    </div>
    """
        
        html += """
</body>
</html>"""
        
        return html
    
    def _generate_markdown(self) -> str:
        """Generate Markdown report."""
        violations = self.results.get("violations", [])
        warnings = self.results.get("warnings", [])
        passed = self.results.get("passed", [])
        
        md = f"""# WCAG Audit Report

## Summary

- **URL:** {self.results.get('base_url', 'Unknown')}
- **Pages Audited:** {self.results.get('pages_audited', 0)}
- **Total Violations:** {self.results.get('total_violations', 0)}
- **Total Warnings:** {self.results.get('total_warnings', 0)}
- **Total Passed:** {self.results.get('total_passed', 0)}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Violations ({len(violations)})

"""
        
        for violation in violations:
            md += f"""### {violation.get('rule', 'Unknown')}

- **WCAG:** {violation.get('wcag', 'Unknown')} (Level {violation.get('level', 'Unknown')})
- **Impact:** {violation.get('impact', 'Unknown')}
- **Description:** {violation.get('description', 'No description')}
- **Element:** `{violation.get('element', 'Unknown')}`
- **Message:** {violation.get('message', 'No message')}
- **Suggestion:** {violation.get('suggestion', 'No suggestion')}

"""
        
        md += f"""## Warnings ({len(warnings)})

"""
        
        for warning in warnings:
            md += f"""- **{warning.get('rule', 'Unknown')}:** {warning.get('message', 'No message')}
"""
        
        md += f"""
## Passed Checks ({len(passed)})

"""
        
        for passed_item in passed:
            md += f"""- **{passed_item.get('rule', 'Unknown')}:** {passed_item.get('description', 'No description')} (WCAG {passed_item.get('wcag', 'Unknown')})
"""
        
        return md
    
    def _generate_text(self) -> str:
        """Generate plain text report."""
        violations = self.results.get("violations", [])
        warnings = self.results.get("warnings", [])
        passed = self.results.get("passed", [])
        
        text = f"""WCAG AUDIT REPORT
==================

URL: {self.results.get('base_url', 'Unknown')}
Pages Audited: {self.results.get('pages_audited', 0)}
Total Violations: {self.results.get('total_violations', 0)}
Total Warnings: {self.results.get('total_warnings', 0)}
Total Passed: {self.results.get('total_passed', 0)}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

VIOLATIONS ({len(violations)})
-----------------

"""
        
        for violation in violations:
            text += f"""Rule: {violation.get('rule', 'Unknown')}
WCAG: {violation.get('wcag', 'Unknown')} (Level {violation.get('level', 'Unknown')})
Impact: {violation.get('impact', 'Unknown')}
Description: {violation.get('description', 'No description')}
Element: {violation.get('element', 'Unknown')}
Message: {violation.get('message', 'No message')}
Suggestion: {violation.get('suggestion', 'No suggestion')}

"""
        
        text += f"""WARNINGS ({len(warnings)})
-----------------

"""
        
        for warning in warnings:
            text += f"""Rule: {warning.get('rule', 'Unknown')}
Message: {warning.get('message', 'No message')}

"""
        
        text += f"""PASSED CHECKS ({len(passed)})
-----------------

"""
        
        for passed_item in passed:
            text += f"""Rule: {passed_item.get('rule', 'Unknown')}
Description: {passed_item.get('description', 'No description')}
WCAG: {passed_item.get('wcag', 'Unknown')} (Level {passed_item.get('level', 'Unknown')})

"""
        
        return text