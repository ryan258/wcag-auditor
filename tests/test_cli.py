"""Tests for the CLI module."""
import pytest
from click.testing import CliRunner
from wcag_auditor.cli import cli
from unittest.mock import patch, MagicMock


class TestCLI:
    """Test cases for CLI commands."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "WCAG Auditor" in result.output
        assert "Audit websites for WCAG 2.2 compliance" in result.output
    
    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output
    
    @patch('wcag_auditor.cli.Auditor')
    def test_audit_command(self, mock_auditor_class):
        """Test audit command."""
        mock_auditor = MagicMock()
        mock_auditor.audit.return_value = {
            "base_url": "https://example.com",
            "pages_audited": 1,
            "total_violations": 0,
            "total_warnings": 0,
            "total_passed": 5,
            "violation_types": {},
            "violations": [],
            "warnings": [],
            "passed": [],
            "pages": []
        }
        mock_auditor_class.return_value = mock_auditor
        
        result = self.runner.invoke(cli, ['audit', 'https://example.com'])
        
        assert result.exit_code == 0
        mock_auditor_class.assert_called_once()
        mock_auditor.audit.assert_called_once()

    @patch('wcag_auditor.cli.Auditor')
    def test_audit_command_supports_vpat(self, mock_auditor_class):
        """VPAT output should be reachable from the public CLI."""
        mock_auditor = MagicMock()
        mock_auditor.audit.return_value = {
            "base_url": "https://example.com",
            "pages_audited": 1,
            "total_violations": 0,
            "total_warnings": 0,
            "total_passed": 5,
            "violation_types": {},
            "violations": [],
            "warnings": [],
            "passed": [],
            "pages": []
        }
        mock_auditor_class.return_value = mock_auditor

        result = self.runner.invoke(cli, ['audit', 'https://example.com', '--format', 'vpat'])

        assert result.exit_code == 0
        assert "Accessibility Conformance Report" in result.output
    
    @patch('wcag_auditor.cli.Auditor')
    def test_check_command(self, mock_auditor_class):
        """Test check command."""
        mock_auditor = MagicMock()
        mock_auditor.audit.return_value = {
            "base_url": "https://example.com",
            "pages_audited": 1,
            "total_violations": 2,
            "total_warnings": 0,
            "total_passed": 3,
            "violation_types": {"missing-alt-text": 2},
            "violations": [
                {
                    "rule": "missing-alt-text",
                    "count": 2,
                    "impact": "critical"
                }
            ],
            "warnings": [],
            "passed": [],
            "pages": []
        }
        mock_auditor_class.return_value = mock_auditor
        
        result = self.runner.invoke(cli, ['check', 'https://example.com'])
        
        assert result.exit_code == 0
        assert "missing-alt-text" in result.output
        assert "2" in result.output

    @patch('wcag_auditor.cli.Auditor')
    def test_check_command_uses_violation_types_for_counts(self, mock_auditor_class):
        """Check summary counts must come from aggregated violation_types."""
        mock_auditor = MagicMock()
        mock_auditor.audit.return_value = {
            "base_url": "https://example.com",
            "pages_audited": 1,
            "total_violations": 2,
            "total_warnings": 0,
            "total_passed": 3,
            "violation_types": {"missing-alt-text": 2},
            "violations": [
                {
                    "rule": "missing-alt-text",
                    "impact": "critical"
                },
                {
                    "rule": "missing-alt-text",
                    "impact": "critical"
                }
            ],
            "warnings": [],
            "passed": [],
            "pages": []
        }
        mock_auditor_class.return_value = mock_auditor

        result = self.runner.invoke(cli, ['check', 'https://example.com'])

        assert result.exit_code == 0
        assert "missing-alt-text" in result.output
        assert "2" in result.output
    
    @patch('wcag_auditor.cli.Auditor')
    def test_summary_command(self, mock_auditor_class):
        """Test summary command."""
        mock_auditor = MagicMock()
        mock_auditor.audit.return_value = {
            "base_url": "https://example.com",
            "pages_audited": 5,
            "total_violations": 10,
            "total_warnings": 2,
            "total_passed": 20,
            "violation_types": {
                "missing-alt-text": 5,
                "empty-links": 3,
                "missing-lang": 2
            },
            "violations": [],
            "warnings": [],
            "passed": [],
            "pages": []
        }
        mock_auditor_class.return_value = mock_auditor
        
        result = self.runner.invoke(cli, ['summary', 'https://example.com'])
        
        assert result.exit_code == 0
        assert "Pages audited: 5" in result.output
        assert "Total violations: 10" in result.output
