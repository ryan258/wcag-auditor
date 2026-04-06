import pytest
from wcag_auditor.rules.perceivable_rules import (
    ComplexAltTextRule, TimeBasedMediaRule, AdaptableLandmarksRule,
    AdaptableReadingSeqRule, FocusAppearanceRule
)

def test_complex_alt_text_rule_svg(page):
    html = """
    <html>
        <body>
            <svg><title>Icon Title</title></svg>
            <svg></svg>
            <div role="img" aria-label="Label"></div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ComplexAltTextRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "missing text alternatives" in violations[0]["message"]

def test_time_based_media_rule(page):
    html = """
    <html>
        <body>
            <video></video>
            <audio><track kind="captions" src="captions.vtt"></audio>
        </body>
    </html>
    """
    page.set_content(html)
    rule = TimeBasedMediaRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "missing a captions track" in violations[0]["message"]

def test_time_based_media_rule_ignores_audio_only(page):
    html = """
    <html>
        <body>
            <audio controls src="podcast.mp3"></audio>
        </body>
    </html>
    """
    page.set_content(html)
    rule = TimeBasedMediaRule()
    violations = rule.evaluate(page)

    assert violations == []

def test_adaptable_landmarks_rule(page):
    html = """
    <html>
        <body>
            <div>No main element here</div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AdaptableLandmarksRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "missing a main landmark" in violations[0]["message"]

def test_reading_sequence_rule(page):
    html = """
    <html>
        <body>
            <div tabindex="5">Positive</div>
            <div tabindex="0">Zero</div>
            <div tabindex="-1">Negative</div>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AdaptableReadingSeqRule()
    violations = rule.evaluate(page)
    
    assert len(violations) == 1
    assert "positive tabindex" in violations[0]["message"]

def test_focus_appearance_rule(page):
    html = """
    <html>
        <head>
            <style>
                .no-outline { outline: none; }
                .good { outline: 2px solid blue; }
            </style>
        </head>
        <body>
            <button class="no-outline">Bad</button>
            <button class="good">Good</button>
            <a href="#">Link</a>
        </body>
    </html>
    """
    page.set_content(html)
    rule = FocusAppearanceRule()
    violations = rule.evaluate(page)
    
    # We heuristically find outline: none
    assert len(violations) >= 1
    assert "no distinct focus indicator" in violations[0]["message"]

def test_focus_appearance_rule_accepts_focus_visible_styles(page):
    html = """
    <html>
        <head>
            <style>
                button { outline: none; }
                button:focus-visible { box-shadow: 0 0 0 3px blue; }
            </style>
        </head>
        <body>
            <button>Good</button>
        </body>
    </html>
    """
    page.set_content(html)
    rule = FocusAppearanceRule()
    violations = rule.evaluate(page)

    assert violations == []

def test_perceivable_rules_happy_path(page):
    html = """
    <html>
        <head>
            <style>
                button, div { outline: 2px solid blue; }
            </style>
        </head>
        <body>
            <main id="main">
                <img src="test.jpg" alt="Valid alt text">
                <video><track kind="captions" src="test.vtt"></video>
                <div tabindex="0">Zero</div>
                <button>Click</button>
            </main>
        </body>
    </html>
    """
    page.set_content(html)
    rule1 = ComplexAltTextRule()
    rule2 = TimeBasedMediaRule()
    rule3 = AdaptableLandmarksRule()
    rule4 = AdaptableReadingSeqRule()
    rule5 = FocusAppearanceRule()
    
    assert len(rule1.evaluate(page)) == 0
    assert len(rule2.evaluate(page)) == 0
    assert len(rule3.evaluate(page)) == 0
    assert len(rule4.evaluate(page)) == 0
    assert len(rule5.evaluate(page)) == 0
