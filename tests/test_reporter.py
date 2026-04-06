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
            "total_manual_reviews": 2,
            "total_warnings": 1,
            "total_passed": 10,
            "violation_types": {
                "missing-alt-text": 2,
                "empty-links": 1
            },
            "manual_review_types": {
                "audio-description-track": 1,
                "accessible-authentication": 1
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
            "manual_reviews": [
                {
                    "rule": "audio-description-track",
                    "wcag": "1.2.5",
                    "level": "AA",
                    "impact": "serious",
                    "description": "Video should expose audio descriptions",
                    "element": "<video></video>",
                    "message": "Video has no detectable audio description track",
                    "suggestion": "Review whether the media requires audio description."
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
                    "template": "/",
                    "page_type": "home",
                    "violations_count": 2,
                    "manual_reviews_count": 1,
                    "warnings_count": 1,
                    "passed_count": 5
                }
            ],
            "sampling": {
                "strategy": "representative",
                "sampled_pages": 5,
                "unique_templates": 3,
                "representative_pages": [
                    {"template": "/", "url": "https://example.com", "page_type": "home", "title": "Home"}
                ]
            },
            "wcag_em": {
                "methodology": "Representative crawl using Playwright.",
                "sample": [
                    {"template": "/", "url": "https://example.com", "page_type": "home"}
                ]
            }
        }
    
    def test_generate_json(self):
        """Test JSON report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("json")
        
        data = json.loads(report)
        assert data["summary"]["base_url"] == "https://example.com"
        assert data["summary"]["total_violations"] == 3
        assert data["summary"]["total_manual_reviews"] == 2
        assert len(data["violations"]) == 2
        assert len(data["manual_reviews"]) == 1
        assert "metadata" in data
    
    def test_generate_html(self):
        """Test HTML report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("html")
        
        assert "<!DOCTYPE html>" in report
        assert "WCAG Audit Report" in report
        assert "https://example.com" in report
        assert "missing-alt-text" in report
        assert "Needs Manual Review" in report
    
    def test_generate_markdown(self):
        """Test Markdown report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("markdown")
        
        assert "# WCAG Audit Report" in report
        assert "**URL:** https://example.com" in report
        assert "missing-alt-text" in report
        assert "WCAG-EM Evaluation Summary" in report
    
    def test_generate_text(self):
        """Test text report generation."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("text")
        
        assert "WCAG AUDIT REPORT" in report
        assert "URL: https://example.com" in report
        assert "missing-alt-text" in report
        assert "Needs Manual Review" in report
        assert "Impact: Unknown" not in report

    def test_render_text_findings_omits_unknown_metadata_for_partial_items(self):
        reporter = Reporter(self.sample_results)
        report = reporter._render_text_findings(
            [{"rule": "low-contrast", "message": "Contrast check not implemented"}],
            "Warnings",
        )

        assert "Rule: low-contrast" in report
        assert "Message: Contrast check not implemented" in report
        assert "WCAG: Unknown" not in report
        assert "Impact: Unknown" not in report
        assert "Description: No description" not in report
    
    def test_generate_invalid_format(self):
        """Test invalid format falls back to text."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("invalid")

        assert "WCAG AUDIT REPORT" in report

    def test_html_no_malformed_tags(self):
        """HTML report must not contain broken tags from earlier bugs."""
        reporter = Reporter(self.sample_results)
        report = reporter.generate("html")

        # The old bugs produced "</n" and "</ WCAG"
        assert "</n" not in report
        assert "</ " not in report

    def test_html_escapes_untrusted_content(self):
        """Page-derived values must be HTML-escaped in the report."""
        evil_results = dict(self.sample_results)
        evil_results["violations"] = [
            {
                "rule": "xss-test",
                "wcag": "1.1.1",
                "level": "A",
                "impact": "critical",
                "description": "test",
                "element": '<img src=x onerror="alert(1)">',
                "message": "<script>alert('xss')</script>",
                "suggestion": "fix it"
            }
        ]
        reporter = Reporter(evil_results)
        report = reporter.generate("html")

        assert "<script>" not in report
        assert "&lt;script&gt;" in report
        assert 'onerror="alert(1)"' not in report

    def test_markdown_includes_remediation_code_when_available(self):
        remediation_results = dict(self.sample_results)
        remediation_results["violations"] = [
            {
                "rule": "missing-alt-text",
                "wcag": "1.1.1",
                "level": "A",
                "impact": "critical",
                "description": "Images must have alternate text",
                "element": "<img>",
                "message": "Missing alt text",
                "suggestion": "Add alt text",
                "remediation_code": '<img alt="Meaningful description">'
            }
        ]

        report = Reporter(remediation_results).generate("markdown")
        assert "```html" in report
        assert "Meaningful description" in report

    def test_generate_json_includes_user_pass_payload(self):
        user_pass_results = dict(self.sample_results)
        user_pass_results["user_pass"] = {
            "status": "completed",
            "provider": "openrouter",
            "pages_reviewed": 1,
            "agents": [{"agent_id": "screen_reader", "model": "openrouter/test"}],
            "findings": [],
            "themes": [],
            "rewrite_suggestions": [],
            "errors": [],
            "limitations": [],
        }

        data = json.loads(Reporter(user_pass_results).generate("json"))
        assert data["user_pass"]["status"] == "completed"
        assert data["user_pass"]["provider"] == "openrouter"

    def test_generate_text_includes_synthetic_user_pass_section(self):
        user_pass_results = dict(self.sample_results)
        user_pass_results["user_pass"] = {
            "status": "completed",
            "provider": "openrouter",
            "pages_reviewed": 1,
            "agents": [{"agent_id": "screen_reader", "model": "openrouter/test"}],
            "findings": [],
            "themes": [
                {
                    "page_url": "https://example.com",
                    "page_title": "Home",
                    "category": "semantics",
                    "target_text": "Start now",
                    "issue": "CTA lacks context",
                    "suggested_change": "Name the audit explicitly",
                    "agent_ids": ["screen_reader"],
                    "confidence": 0.8,
                }
            ],
            "rewrite_suggestions": [
                {
                    "page_url": "https://example.com",
                    "location": "Primary CTA",
                    "current_text": "Start now",
                    "proposed_text": "Start your accessibility audit",
                    "rationale": "More specific wording.",
                }
            ],
            "errors": [],
            "limitations": ["Synthetic reviewers are not a substitute for human participants."],
        }

        report = Reporter(user_pass_results).generate("text")
        assert "SYNTHETIC USER PASS" in report
        assert "Start your accessibility audit" in report
