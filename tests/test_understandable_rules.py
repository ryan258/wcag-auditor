import pytest
from wcag_auditor.rules.understandable_rules import (
    InputAssistanceRule, IdentifyInputPurposeRule
)

def test_input_assistance_rule(page):
    html = """
    <html>
        <body>
            <input type="text" aria-invalid="true" aria-errormessage="err1">
            <input type="text" aria-invalid="true">
            <span id="err1">Error text</span>
        </body>
    </html>
    """
    page.set_content(html)
    rule = InputAssistanceRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "lacks an associated error message" in violations[0]["message"]

def test_identify_input_purpose_rule(page):
    html = """
    <html>
        <body>
            <form>
                <input type="text" name="shipping_address" autocomplete="shipping street-address">
                <input type="text" name="billing_address">
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = IdentifyInputPurposeRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "missing an autocomplete attribute" in violations[0]["message"]

def test_understandable_rules_happy_path(page):
    html = """
    <html>
        <body>
            <form>
                <input type="text" name="shipping_address" autocomplete="shipping street-address">
                <input type="text" aria-invalid="true" aria-errormessage="err1">
                <span id="err1">Error text</span>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule1 = InputAssistanceRule()
    rule2 = IdentifyInputPurposeRule()
    
    assert len(rule1.evaluate(page)) == 0
    assert len(rule2.evaluate(page)) == 0
