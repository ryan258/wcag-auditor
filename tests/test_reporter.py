"""Tests for the reporter module."""
import pytest
import json
from wcag_auditor.reporter import Reporter


class TestReporter:
    """Test cases for Reporter class."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_results = {
            "base_url": "https://example.com",
            "pages_audited": 5,
            "total_violations": 3,
            "total_warnings": 1,
            "total_passed": 10,
            "violation_types": {
                "missing-alt-text": 2,
                "empty-links": 1
            },
            "violations": [
                {
                    "rule": "missing-alt-text",
                    "wcag": "1.1.1",
                    "level": "A",
                    "impact": "critical",
                    "description": "Images must have alternate text",
                    "element": "<img src=\"test.jpg\">",
                    "message": "Image missing alt attribute",
                    "suggestion": "Add descriptive alt text"
                },
                {
                    "rule": "empty-links",
                    "wcag": "2.4.4",
                    "level": "A",
                    "impact": "serious",
                    "description": "Links must have discernible text",
                    "element": "<a href=\"/page\"></a>",
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content"
                }
            ],
            "warnings": [
                {
                    "rule": "low-contrast",
                    "message": "Contrast check not implemented"
                }
            ],
            "passed": [
                {
                    "rule": "missing-lang",
                    "wcag": "3.1.1",
                    "level": "A",
                    "description": "Page must have a lang attribute"
                }
            ],
            "pages": [
                {
                    "url": "https://example.com",
                    "title": "Home",
                    "violations_count": 2,
                    "warnings_count": 1,
                    "passed_count": 5
                }
            ]
        }
    
    def test_generate_json(self):
        """Test JSON report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("json")
        
        data = json.loads(report)
        assert data["summary"]["base_url"] == "https://example.com"
        assert data["summary"]["total_violations"] == 3
        assert len(data["violations"]) == 2
        assert "metadata" in data
    
    def test_generate_html(self):
        """Test HTML report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("html")
        
        assert "<!DOCTYPE html>" in report
        assert "WCAG Audit Report" in report
        assert "https://example.com" in report
        assert "missing-alt-text" in report
    
    def test_generate_markdown(self):
        """Test Markdown report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("markdown")
        
        assert "# WCAG Audit Report" in report
        assert "**URL:** https://example.com" in report
        assert "missing-alt-text" in report
    
    def test_generate_text(self):
        """Test text report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("text")
        
        assert "WCAG AUDIT REPORT" in report
        assert "URL: https://example.com" in report
        assert "missing-alt-text" in report
    
    def test_generate_invalid_format(self):
        """Test invalid format falls back to text."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("invalid")
        
        assert "WCAG AUDIT REPORT" in report