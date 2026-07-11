import pytest
from wcag_auditor.rules.perceivable_rules import (
    ComplexAltTextRule, TimeBasedMediaRule, AdaptableLandmarksRule,
    AdaptableReadingSeqRule, AudioDescriptionRule, ContrastMinimumRule,
    FocusAppearanceRule, InlineLanguageChangeRule
)
from wcag_auditor.rules.helpers import selector_for_html_snippet

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
    assert "captions or subtitles track" in violations[0]["message"]

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

def test_time_based_media_rule_flags_invalid_caption_track(page):
    html = """
    <html>
        <body>
            <video>
                <track kind="captions" src="">
            </video>
        </body>
    </html>
    """
    page.set_content(html)
    rule = TimeBasedMediaRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert "Caption track source is empty" in findings[0]["message"]

def test_audio_description_rule_marks_missing_track_for_review(page):
    html = """
    <html>
        <body>
            <video>
                <track kind="captions" src="captions.vtt">
            </video>
        </body>
    </html>
    """
    page.set_content(html)
    rule = AudioDescriptionRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "audio description track" in findings[0]["message"]

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

def test_contrast_minimum_rule(page):
    html = """
    <html>
        <head>
            <style>
                .bad { color: rgb(120, 120, 120); background: rgb(150, 150, 150); }
                .good { color: rgb(0, 0, 0); background: rgb(255, 255, 255); }
            </style>
        </head>
        <body>
            <p class="bad">Low contrast text</p>
            <p class="good">Readable text</p>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ContrastMinimumRule()
    violations = rule.evaluate(page)

    assert len(violations) == 1
    assert "contrast ratio" in violations[0]["message"]

def test_contrast_minimum_rule_happy_path(page):
    html = """
    <html>
        <head>
            <style>
                .good { color: rgb(0, 0, 0); background: rgb(255, 255, 255); }
            </style>
        </head>
        <body>
            <p class="good">Readable text</p>
        </body>
    </html>
    """
    page.set_content(html)
    rule = ContrastMinimumRule()

    assert rule.evaluate(page) == []


def test_contrast_rule_does_not_treat_a_stacking_context_as_an_overlap(page):
    page.set_content(
        """
        <style>
            .stacking-context { position: relative; z-index: 1; background: rgb(150, 150, 150); }
            .bad { color: rgb(120, 120, 120); }
        </style>
        <div class="stacking-context"><p class="bad">Low contrast text</p></div>
        """
    )

    findings = ContrastMinimumRule().evaluate(page)

    assert len(findings) == 1
    assert findings[0].get("finding_type") != "needs_review"
    assert "contrast ratio" in findings[0]["message"]


def test_selector_for_html_snippet_returns_only_unambiguous_matches(page):
    page.set_content(
        '<button class="unique">Save</button>'
        '<span>Duplicate</span><span>Duplicate</span>'
    )

    selector = selector_for_html_snippet(page, '<button class="unique">Save</button>')
    assert selector is not None
    assert page.locator(selector).count() == 1
    assert selector_for_html_snippet(page, "<span>Duplicate</span>") is None

def test_inline_language_change_rule(page):
    html = """
    <html lang="en">
        <body>
            <p>Hello <span>Señor</span></p>
            <p><span lang="fr">Bonjour</span></p>
        </body>
    </html>
    """
    page.set_content(html)
    rule = InlineLanguageChangeRule()
    findings = rule.evaluate(page)

    assert len(findings) == 1
    assert findings[0]["finding_type"] == "needs_review"
    assert "switch language" in findings[0]["message"]

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
                <video>
                    <track kind="captions" src="test.vtt">
                    <track kind="descriptions" src="desc.vtt">
                </video>
                <div tabindex="0">Zero</div>
                <p><span lang="fr">Bonjour</span></p>
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
    rule6 = AudioDescriptionRule()
    
    assert len(rule1.evaluate(page)) == 0
    assert len(rule2.evaluate(page)) == 0
    assert len(rule3.evaluate(page)) == 0
    assert len(rule4.evaluate(page)) == 0
    assert len(rule5.evaluate(page)) == 0
    assert len(rule6.evaluate(page)) == 0
