import pytest
from wcag_auditor.rules.understandable_rules import (
    PredictableNavigationRule, InputAssistanceRule, LabelsInstructionsRule,
    ErrorSuggestionRule, RequiredFieldIndicatorsRule, RedundantEntryRule,
    AccessibleAuthenticationRule, IdentifyInputPurposeRule
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

def test_predictable_navigation_rule(page):
    html = """
    <html>
        <body>
            <select onchange="window.location='/next'">
                <option>Choose</option>
            </select>
        </body>
    </html>
    """
    page.set_content(html)
    rule = PredictableNavigationRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "value changes" in violations[0]["message"]

def test_labels_instructions_and_required_indicator_rules(page):
    html = """
    <html>
        <body>
            <form>
                <label for="password">Password</label>
                <input id="password" type="password" required>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    instructions = LabelsInstructionsRule().evaluate(page)
    required = RequiredFieldIndicatorsRule().evaluate(page)

    assert len(instructions) == 1
    assert "format guidance" in instructions[0]["message"]
    assert len(required) == 1
    assert "Required field" in required[0]["message"]

def test_error_suggestion_rule(page):
    html = """
    <html>
        <body>
            <input type="email" aria-invalid="true" aria-errormessage="err1">
            <span id="err1">Email is invalid.</span>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ErrorSuggestionRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "does not suggest how to fix it" in violations[0]["message"]

def test_redundant_entry_rule(page):
    html = """
    <html>
        <body>
            <form>
                <label>Shipping address <input type="text" name="shipping_address"></label>
                <label>Billing address <input type="text" name="billing_address"></label>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = RedundantEntryRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "more than once" in findings[0]["message"]

def test_accessible_authentication_rule(page):
    html = """
    <html>
        <body>
            <form>
                <label>Password <input type="password"></label>
                <p>Solve 3 + 4 to continue</p>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AccessibleAuthenticationRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "cognitive challenge" in violations[0]["message"]

def test_accessible_authentication_rule_flags_visible_captcha(page):
    html = """
    <html>
        <body>
            <form>
                <label>Email <input type="email"></label>
                <label>Password <input type="password"></label>
                <div class="g-recaptcha" data-sitekey="demo" style="width: 320px; height: 78px;"></div>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AccessibleAuthenticationRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "CAPTCHA" in findings[0]["message"]

def test_accessible_authentication_rule_ignores_standard_login(page):
    html = """
    <html>
        <body>
            <form>
                <label>Email <input type="email"></label>
                <label>Password <input type="password"></label>
                <button type="submit">Sign in</button>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AccessibleAuthenticationRule()

    assert rule.evaluate(page) == []

def test_accessible_authentication_rule_ignores_hidden_captcha_plumbing(page):
    html = """
    <html>
        <body>
            <form>
                <label>Email <input type="email"></label>
                <label>Password <input type="password"></label>
                <input type="hidden" name="captcha_token" value="opaque-token">
                <button type="submit">Sign in</button>
            </form>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AccessibleAuthenticationRule()

    assert rule.evaluate(page) == []

def test_predictable_navigation_rule_happy_path(page):
    html = """
    <html>
        <body>
            <select onchange="validateChoice()">
                <option>Choose</option>
            </select>
            <button type="submit">Continue</button>
        </body>
    </html>
    """
    page.set_content(html)
    rule = PredictableNavigationRule()

    assert rule.evaluate(page) == []

def test_error_suggestion_rule_happy_path(page):
    html = """
    <html>
        <body>
            <input type="email" aria-invalid="true" aria-errormessage="err1">
            <span id="err1">Enter a valid email address, for example name@example.com.</span>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ErrorSuggestionRule()

    assert rule.evaluate(page) == []

def test_form_guidance_rules_happy_path(page):
    html = """
    <html>
        <body>
            <form>
                <label for="password">Password (required)</label>
                <p id="password-help">Use at least 12 characters.</p>
                <input id="password" type="password" required aria-describedby="password-help">
                <label>Shipping address <input type="text" name="shipping_address" autocomplete="shipping street-address"></label>
                <label>Billing address <input type="text" name="billing_address" autocomplete="billing street-address"></label>
                <label><input type="checkbox" name="same_as_shipping"> Billing address is the same as shipping</label>
            </form>
        </body>
    </html>
    """
    page.set_content(html)

    assert LabelsInstructionsRule().evaluate(page) == []
    assert RequiredFieldIndicatorsRule().evaluate(page) == []
    assert RedundantEntryRule().evaluate(page) == []

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
