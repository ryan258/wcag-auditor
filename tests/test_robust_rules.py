import pytest
from wcag_auditor.rules.robust_rules import (
    ARIAValidationRule, StatusMessagesRule
)

def test_aria_validation_rule(page):
    html = """
    <html>
        <body>
            <div role="combobox" aria-expanded="false" aria-controls="list1"></div>
            <div role="combobox" aria-expanded="false"></div>
            <div role="checked"></div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ARIAValidationRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 2
    messages = [v["message"] for v in violations]
    assert any("needs both aria-expanded and aria-controls" in m for m in messages)
    assert any("Invalid ARIA role" in m for m in messages)

def test_status_messages_rule(page):
    html = """
    <html>
        <body>
            <div class="alert" role="alert">Error</div>
            <div class="alert">Success</div>
            <div class="toast" aria-live="polite">Toast</div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = StatusMessagesRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "not exposed to assistive tech" in violations[0]["message"]

def test_robust_rules_happy_path(page):
    html = """
    <html>
        <body>
            <div role="combobox" aria-expanded="false" aria-controls="list1">Combobox</div>
            <div class="toast" aria-live="polite">Toast</div>
        </body>
    </html>
    """
    page.set_content(html)
    aria_rule = ARIAValidationRule()
    status_rule = StatusMessagesRule()
    
    assert len(aria_rule.evaluate(page)) == 0
    assert len(status_rule.evaluate(page)) == 0
