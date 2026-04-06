"""Tests for the auditor module and rules."""
import pytest
from unittest.mock import Mock, patch
from wcag_auditor.auditor import Auditor
from wcag_auditor.rules.core_rules import (
    MissingAltTextRule, MissingLabelsRule, MissingLangRule,
    EmptyLinksRule, EmptyButtonsRule, MissingTitleRule, AutofocusInputsRule
)

# Rule Evaluation Tests

def test_check_missing_alt_text(page):
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
    page.set_content(html)
    rule = MissingAltTextRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "Image missing alt attribute" in violations[0]["message"]

def test_alt_empty_string_is_valid(page):
    """alt="" is the WCAG-correct pattern for decorative images."""
    html = """
    <html>
        <body>
            <img src="decorative.jpg" alt="">
        </body>
    </html>
    """
    page.set_content(html)
    rule = MissingAltTextRule()
    violations = rule.evaluate(page)
    assert len(violations) == 0

def test_check_missing_labels(page):
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
    page.set_content(html)
    rule = MissingLabelsRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "Form input missing label" in violations[0]["message"]

def test_implicit_label_is_valid(page):
    """An input wrapped in <label> should not be flagged."""
    html = """
    <html>
        <body>
            <label>Name <input type="text"></label>
        </body>
    </html>
    """
    page.set_content(html)
    rule = MissingLabelsRule()
    violations = rule.evaluate(page)
    assert len(violations) == 0

def test_check_missing_lang(page):
    """Test missing lang attribute detection."""
    html = """
    <html>
        <head><title>Test</title></head>
        <body></body>
    </html>
    """
    page.set_content(html)
    rule = MissingLangRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "HTML element missing lang attribute" in violations[0]["message"]

def test_check_empty_links(page):
    """Test empty links detection."""
    html = """
    <html>
        <body>
            <a href="/page1">Good link</a>
            <a href="/page2"></a>
            <a href="/page3" aria-label="Good"></a>
            <a href="/page4"><img src="icon.png" alt=""></a>
            <a href="/page5"><img src="icon.png" alt="Icon"></a>
        </body>
    </html>
    """
    page.set_content(html)
    rule = EmptyLinksRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 2
    messages = [v["message"] for v in violations]
    assert "Link has no discernible text" in messages[0]

def test_check_empty_buttons(page):
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
    page.set_content(html)
    rule = EmptyButtonsRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "Button has no discernible text" in violations[0]["message"]

def test_check_missing_title(page):
    """Test missing title detection."""
    html = """
    <html>
        <head></head>
        <body></body>
    </html>
    """
    page.set_content(html)
    rule = MissingTitleRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "Page missing title element or title is empty" in violations[0]["message"]

def test_autofocus_inputs(page):
    html = """
    <html>
        <body><input type="text" autofocus></body>
    </html>
    """
    page.set_content(html)
    rule = AutofocusInputsRule()
    violations = rule.evaluate(page)
    assert len(violations) == 1

# Auditor Integration Tests

class MockPage:
    def __init__(self):
        self.routes = []
        self._title = "Test Title"
        
    def goto(self, url, **kwargs):
        if "error" in url:
            raise Exception("Mocked Network Error")
            
    def title(self):
        return self._title
        
    def evaluate(self, script):
        if "document.links" in script or "Array.from" in script:
            return ["https://example.com/page1", "https://example.com/page2", "https://other.com/page"]
        return []
        
    def locator(self, sel):
        class MockLocator:
            def all(self): return []
            def count(self): return 0
        return MockLocator()

class MockContext:
    def new_page(self):
        return MockPage()
    def close(self): pass

class MockBrowser:
    def new_context(self, **kwargs):
        return MockContext()
    def close(self): pass

class MockPlaywright:
    @property
    def chromium(self):
        class Chrome:
            def launch(self, **kwargs):
                return MockBrowser()
        return Chrome()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@patch('wcag_auditor.auditor.sync_playwright')
def test_auditor_init_and_audit(mock_pw):
    """Test auditor initialization and core behavior via mock playwright."""
    mock_pw.return_value = MockPlaywright()
    
    auditor = Auditor("https://example.com", max_depth=1, max_pages=10)
    assert auditor.base_url == "https://example.com"
    
    results = auditor.audit()
    assert results["pages_audited"] > 0
    assert "pages" in results

@patch('wcag_auditor.auditor.sync_playwright')
def test_audit_resets_state_on_reuse(mock_pw):
    """Reusing an Auditor instance should not carry stale state."""
    mock_pw.return_value = MockPlaywright()
    
    auditor = Auditor("https://example.com", max_depth=0, max_pages=10)
    result1 = auditor.audit()
    assert result1["pages_audited"] == 1
    
    result2 = auditor.audit()
    assert result2["pages_audited"] == 1

@patch('wcag_auditor.auditor.sync_playwright')
def test_audit_execution_failure(mock_pw):
    mock_pw.side_effect = Exception("Playwright bin missing")
    auditor = Auditor("https://example.com")
    res = auditor.audit()
    
    assert res["pages_audited"] == 0
    assert "base_url" in res
    assert "violations" in res
    assert "pages" in res
    
    warnings = [w["rule"] for w in res["warnings"]]
    assert "execution-failure" in warnings