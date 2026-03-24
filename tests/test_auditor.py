"""Tests for the auditor module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from wcag_auditor.auditor import Auditor, AuditResult
from bs4 import BeautifulSoup


class TestAuditor:
    """Test cases for Auditor class."""
    
    def test_init(self):
        """Test auditor initialization."""
        auditor = Auditor("https://example.com", max_depth=3, max_pages=100)
        assert auditor.base_url == "https://example.com"
        assert auditor.max_depth == 3
        assert auditor.max_pages == 100
        assert auditor.base_domain == "example.com"
        assert auditor.scheme == "https"
    
    @patch('wcag_auditor.auditor.requests.get')
    def test_get_page_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response
        
        auditor = Auditor("https://example.com")
        soup = auditor._get_page("https://example.com")
        
        assert soup is not None
        assert soup.find("body").get_text() == "Test"
    
    @patch('wcag_auditor.auditor.requests.get')
    def test_get_page_failure(self, mock_get):
        """Test failed page fetch."""
        mock_get.side_effect = Exception("Network error")
        
        auditor = Auditor("https://example.com")
        soup = auditor._get_page("https://example.com")
        
        assert soup is None
    
    def test_check_missing_alt_text(self):
        """Test missing alt text detection."""
        html = """
        <html>
            <body>
                <img src="test.jpg">
                <img src="test2.jpg" alt="Good">
                <img src="test3.jpg" role="presentation">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_alt_text(soup)
        
        assert len(violations) == 1
        assert "Image missing alt attribute" in violations[0]["message"]
    
    def test_check_missing_labels(self):
        """Test missing labels detection."""
        html = """
        <html>
            <body>
                <input type="text" id="test1">
                <label for="test1">Good</label>
                <input type="text" id="test2">
                <input type="text" aria-label="Good">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_labels(soup)
        
        assert len(violations) == 1
        assert "Form input missing label" in violations[0]["message"]
    
    def test_check_missing_lang(self):
        """Test missing lang attribute detection."""
        html = """
        <html>
            <head><title>Test</title></head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_lang(soup)
        
        assert len(violations) == 1
        assert "HTML element missing lang attribute" in violations[0]["message"]
    
    def test_check_empty_links(self):
        """Test empty links detection."""
        html = """
        <html>
            <body>
                <a href="/page1">Good link</a>
                <a href="/page2"></a>
                <a href="/page3" aria-label="Good"></a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_empty_links(soup)
        
        assert len(violations) == 1
        assert "Link has no discernible text" in violations[0]["message"]
    
    def test_check_empty_buttons(self):
        """Test empty buttons detection."""
        html = """
        <html>
            <body>
                <button>Good button</button>
                <button></button>
                <button aria-label="Good"></button>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_empty_buttons(soup)
        
        assert len(violations) == 1
        assert "Button has no discernible text" in violations[0]["message"]
    
    def test_check_missing_title(self):
        """Test missing title detection."""
        html = """
        <html>
            <head></head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_title(soup)
        
        assert len(violations) == 1
        assert "Page missing title element" in violations[0]["message"]
    
    def test_extract_links(self):
        """Test link extraction."""
        html = """
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="https://example.com/page2">Link 2</a>
                <a href="https://other.com/page3">External</a>
                <a href="#section">Fragment</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        links = auditor._extract_links(soup, "https://example.com")
        
        assert len(links) == 2
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://other.com/page3" not in links
        assert "https://example.com#section" not in links

    def test_alt_empty_string_is_valid(self):
        """alt="" is the WCAG-correct pattern for decorative images."""
        html = """
        <html>
            <body>
                <img src="decorative.jpg" alt="">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_alt_text(soup)

        assert len(violations) == 0

    def test_implicit_label_is_valid(self):
        """An input wrapped in <label> should not be flagged."""
        html = """
        <html>
            <body>
                <label>Name <input type="text"></label>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_missing_labels(soup)

        assert len(violations) == 0

    def test_link_with_empty_alt_img_is_violation(self):
        """<a><img alt=""></a> has no discernible text and must be flagged."""
        html = """
        <html>
            <body>
                <a href="/page"><img src="icon.png" alt=""></a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_empty_links(soup)

        assert len(violations) == 1

    def test_link_with_nonempty_alt_img_passes(self):
        """<a><img alt="Home"></a> provides discernible text."""
        html = """
        <html>
            <body>
                <a href="/"><img src="logo.png" alt="Home"></a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        auditor = Auditor("https://example.com")
        violations = auditor._check_empty_links(soup)

        assert len(violations) == 0

    @patch('wcag_auditor.auditor.requests.get')
    def test_contrast_skipped_as_warning(self, mock_get):
        """Contrast check must surface as a skipped warning, not a pass."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html lang='en'><head><title>T</title></head><body></body></html>"
        mock_get.return_value = mock_response

        auditor = Auditor("https://example.com", max_depth=0)
        results = auditor.audit()

        passed_rules = [p["rule"] for p in results["passed"]]
        warning_rules = [w["rule"] for w in results["warnings"]]

        assert "low-contrast" not in passed_rules
        assert "low-contrast" in warning_rules

    @patch('wcag_auditor.auditor.requests.get')
    def test_contrast_warning_emitted_once_on_multipage(self, mock_get):
        """The low-contrast skip notice must appear exactly once, not per page."""
        page_html = "<html lang='en'><head><title>T</title></head><body><a href='/p2'>link</a></body></html>"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = page_html
        mock_get.return_value = mock_response

        auditor = Auditor("https://example.com", max_depth=1, max_pages=5)
        results = auditor.audit()

        contrast_warnings = [w for w in results["warnings"] if w["rule"] == "low-contrast"]
        assert len(contrast_warnings) == 1

    @patch('wcag_auditor.auditor.requests.get')
    def test_audit_resets_state_on_reuse(self, mock_get):
        """Reusing an Auditor instance should not carry stale state."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html lang='en'><head><title>T</title></head><body></body></html>"
        mock_get.return_value = mock_response

        auditor = Auditor("https://example.com", max_depth=0)
        result1 = auditor.audit()
        assert result1["pages_audited"] == 1

        result2 = auditor.audit()
        assert result2["pages_audited"] == 1  # must not be 0