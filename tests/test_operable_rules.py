import pytest
from wcag_auditor.rules.operable_rules import (
    KeyboardAccessibilityRule, NavigableRule, TargetSizeRule
)

def test_keyboard_accessibility_rule(page):
    html = """
    <html>
        <body>
            <div onclick="alert('click')">Div Click</div>
            <button onclick="alert('click')">Button Click</button>
            <div tabindex="0" onclick="alert('click')" onkeydown="alert('click')">Accessible Div Click</div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = KeyboardAccessibilityRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "lacks keyboard event handlers" in violations[0]["message"]

def test_navigable_rule(page):
    html = """
    <html>
        <body>
            <a href="#main" class="skip-link">Skip to Content</a>
            <main id="main">
                <iframe src="test.html"></iframe>
            </main>
        </body>
    </html>
    """
    page.set_content(html)
    rule = NavigableRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "Iframe missing title attribute" in violations[0]["message"]

def test_navigable_rule_missing_skip_link(page):
    html = """
    <html>
        <body>
            <main id="main">
                <p>Hello world</p>
            </main>
        </body>
    </html>
    """
    page.set_content(html)
    rule = NavigableRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "missing a 'Skip to Content' link" in violations[0]["message"]

def test_target_size_rule(page):
    html = """
    <html>
        <head>
            <style>
                .small { width: 10px; height: 10px; }
                .large { width: 44px; height: 44px; }
            </style>
        </head>
        <body>
            <button class="small">Small</button>
            <button class="large">Large</button>
        </body>
    </html>
    """
    page.set_content(html)
    rule = TargetSizeRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "less than 24x24" in violations[0]["message"]

def test_operable_rules_happy_path(page):
    html = """
    <html>
        <head>
            <style>
                button { width: 44px; height: 44px; }
                .skip-link { display: inline-block; min-width: 44px; min-height: 44px; }
            </style>
        </head>
        <body>
            <a href="#main" class="skip-link">Skip to Content</a>
            <main id="main">
                <button onclick="alert('click')">Button Click</button>
                <div tabindex="0" onclick="alert('click')" onkeydown="alert('click')">Accessible Div Click</div>
                <iframe src="test.html" title="Test Frame"></iframe>
            </main>
        </body>
    </html>
    """
    page.set_content(html)
    rule1 = KeyboardAccessibilityRule()
    rule2 = NavigableRule()
    rule3 = TargetSizeRule()
    
    assert len(rule1.evaluate(page)) == 0
    assert len(rule2.evaluate(page)) == 0
    assert len(rule3.evaluate(page)) == 0
