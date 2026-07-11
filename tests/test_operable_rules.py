import pytest
from wcag_auditor.rules.operable_rules import (
    KeyboardAccessibilityRule,
    KeyboardTrapRule,
    EnoughTimeRule,
    NavigableRule,
    LinkPurposeRule,
    FocusNotObscuredRule,
    PointerGesturesRule,
    PointerCancellationRule,
    DraggingMovementsRule,
    TargetSizeRule,
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


def test_keyboard_accessibility_rule_reviews_non_focusable_button_roles(page):
    page.set_content('<div role="button" style="cursor: pointer">Open menu</div>')

    findings = KeyboardAccessibilityRule().evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "not keyboard focusable" in findings[0]["message"]


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


def test_keyboard_trap_rule(page):
    html = """
    <html>
        <body>
            <div role="dialog">
                <input type="text">
            </div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = KeyboardTrapRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "keyboard trap" in findings[0]["message"]


def test_enough_time_rule(page):
    html = """
    <html>
        <body>
            <div class="carousel" data-auto-rotate="true">
                <div>Slide 1</div>
            </div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = EnoughTimeRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "pause, stop, or resume control" in violations[0]["message"]


def test_enough_time_rule_happy_path(page):
    html = """
    <html>
        <body>
            <div class="carousel" data-auto-rotate="true">
                <div>Slide 1</div>
                <button type="button">Pause rotation</button>
            </div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = EnoughTimeRule()

    assert rule.evaluate(page) == []


def test_enough_time_rule_recognizes_spanish_pause_control(page):
    page.set_content(
        '<html lang="es"><div class="carousel" data-auto-rotate="true">'
        '<button type="button">Pausar rotación</button></div></html>'
    )

    assert EnoughTimeRule().evaluate(page) == []


def test_enough_time_rule_routes_unknown_languages_to_review(page):
    page.set_content(
        '<html lang="fr"><div class="carousel" data-auto-rotate="true"></div></html>'
    )

    findings = EnoughTimeRule().evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"


def test_link_purpose_rule(page):
    html = """
    <html>
        <body>
            <a href="/one">Read more</a>
            <a href="/two">Read more</a>
        </body>
    </html>
    """
    page.set_content(html)
    rule = LinkPurposeRule()
    violations = rule.evaluate(page)

    assert len(violations) == 2
    assert "generic" in violations[0]["message"]


def test_link_purpose_rule_happy_path(page):
    html = """
    <html>
        <body>
            <a href="/pricing">View pricing plans</a>
        </body>
    </html>
    """
    page.set_content(html)
    rule = LinkPurposeRule()

    assert rule.evaluate(page) == []


def test_link_purpose_rule_recognizes_spanish_generic_text(page):
    page.set_content(
        '<html lang="es"><a href="/one">Leer más</a><a href="/two">Leer más</a></html>'
    )

    findings = LinkPurposeRule().evaluate(page)

    assert len(findings) == 2
    assert all(finding.get("finding_type") != "needs_review" for finding in findings)


def test_link_purpose_rule_routes_unknown_languages_to_review(page):
    page.set_content('<html lang="fr"><a href="/one">En savoir plus</a></html>')

    findings = LinkPurposeRule().evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"


def test_focus_not_obscured_rule(page):
    html = """
    <html>
        <head>
            <style>
                body { margin: 0; }
                .header { position: fixed; top: 0; left: 0; right: 0; height: 80px; background: black; z-index: 10; }
                .target { display: inline-block; margin-top: 0; }
                main { padding-top: 0; }
            </style>
        </head>
        <body>
            <div class="header"></div>
            <main>
                <a class="target" href="#target">Target</a>
            </main>
        </body>
    </html>
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    page.set_content(html)
    rule = FocusNotObscuredRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "obscured" in violations[0]["message"]


def test_focus_not_obscured_rule_restores_page_state_after_focusing(page):
    html = """
    <html>
        <head>
            <style>
                body { margin: 0; }
                .header { position: fixed; top: 0; left: 0; right: 0; height: 80px; background: black; z-index: 10; }
            </style>
            <script>
                window.focusEvents = 0;
                window.scrollEvents = 0;
                document.addEventListener('focusin', () => { window.focusEvents += 1; }, true);
                window.addEventListener('scroll', () => { window.scrollEvents += 1; });
            </script>
        </head>
        <body>
            <div class="header"></div>
            <main>
                <a class="target" href="#target">Target</a>
            </main>
        </body>
    </html>
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    page.set_content(html)
    FocusNotObscuredRule().evaluate(page)
    state = page.evaluate("""() => ({
            focusEvents: window.focusEvents,
            scrollEvents: window.scrollEvents,
            activeTag: document.activeElement ? document.activeElement.tagName : null,
        })""")

    assert state["focusEvents"] > 0
    assert state["activeTag"] == "BODY"


def test_focus_pointer_and_dragging_rules_happy_path(page):
    html = """
    <html>
        <head>
            <style>
                body { margin: 0; }
                .header { position: fixed; top: 0; left: 0; right: 0; height: 80px; background: black; z-index: 10; }
                main { padding-top: 120px; }
            </style>
        </head>
        <body>
            <div class="header"></div>
            <main>
                <a href="#target">Visible target</a>
            </main>
            <section data-gesture="swipe-left">
                <button type="button">Next slide</button>
            </section>
            <button type="button" onpointerdown="start()" onpointerup="finish()">Save</button>
            <ul>
                <li draggable="true">
                    Drag me
                    <button type="button" aria-label="Move item up">Move up</button>
                </li>
            </ul>
        </body>
    </html>
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    page.set_content(html)

    assert FocusNotObscuredRule().evaluate(page) == []
    assert PointerGesturesRule().evaluate(page) == []
    assert PointerCancellationRule().evaluate(page) == []
    assert DraggingMovementsRule().evaluate(page) == []


def test_pointer_and_dragging_rules(page):
    html = """
    <html>
        <body>
            <div data-gesture="swipe-left"></div>
            <div onpointerdown="startDrag()"></div>
            <div draggable="true">Drag me</div>
        </body>
    </html>
    """
    page.set_content(html)

    gesture_findings = PointerGesturesRule().evaluate(page)
    pointer_findings = PointerCancellationRule().evaluate(page)
    dragging_findings = DraggingMovementsRule().evaluate(page)

    assert len(gesture_findings) == 1
    assert gesture_findings[0]["finding_type"] == "needs_review"
    assert len(pointer_findings) == 1
    assert "down event" in pointer_findings[0]["message"]
    assert len(dragging_findings) == 1
    assert dragging_findings[0]["finding_type"] == "needs_review"


def test_pointer_cancellation_rule_reviews_custom_pointer_controls(page):
    page.set_content('<div role="button" style="cursor: pointer">Save</div>')

    findings = PointerCancellationRule().evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "custom pointer control" in findings[0]["message"]


def test_pointer_cancellation_rule_limits_findings(page):
    html = "<html><body>{}</body></html>".format(
        '<div onpointerdown="start()"></div>' * 12
    )
    page.set_content(html)
    findings = PointerCancellationRule().evaluate(page)

    assert len(findings) == 12


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
