from typing import List, Dict, Any
from playwright.sync_api import Page
from . import AbstractRule, RuleMetadata
from .perceivable_rules import (
    ComplexAltTextRule,
    TimeBasedMediaRule,
    AdaptableLandmarksRule,
    AdaptableReadingSeqRule,
    ContrastMinimumRule,
    FocusAppearanceRule
)
from .operable_rules import (
    KeyboardAccessibilityRule,
    NavigableRule,
    TargetSizeRule
)
from .understandable_rules import (
    InputAssistanceRule,
    IdentifyInputPurposeRule
)
from .robust_rules import (
    ARIAValidationRule,
    StatusMessagesRule
)

class MissingLabelsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="missing-labels",
            description="Form elements must have labels",
            wcag_criterion="3.3.2", # updated reflecting reality and 2.2 roadmap
            level="A",
            impact="serious",
            applicability="form"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("input, select, textarea").all()
        for loc in locators:
            type_attr = loc.get_attribute("type")
            if type_attr in ["hidden", "submit", "button", "reset", "image"]:
                continue
            
            # Check implicit and explicit labels via JS
            has_label = loc.evaluate("""el => {
                if (el.labels && el.labels.length > 0) return true;
                if (el.hasAttribute('aria-label')) return true;
                if (el.hasAttribute('aria-labelledby')) return true;
                return false;
            }""")
            
            if not has_label:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Form input missing label",
                    "suggestion": "Add a <label> element, wrap the input in a <label>, or use aria-label"
                })
        return violations

class MissingLangRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="missing-lang",
            description="Page must have a lang attribute",
            wcag_criterion="3.1.1",
            level="A",
            impact="serious",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locator = page.locator("html")
        if locator.count() > 0:
            lang = locator.first.get_attribute("lang")
            if not lang:
                html_snippet = locator.first.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "HTML element missing lang attribute",
                    "suggestion": 'Add lang attribute to <html> element (e.g., <html lang="en">)'
                })
        return violations

class EmptyLinksRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="empty-links",
            description="Links must have discernible text",
            wcag_criterion="2.4.4",
            level="A",
            impact="serious",
            applicability="link"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("a").all()
        for loc in locators:
            has_discernible_text = loc.evaluate("""el => {
                if (el.textContent.trim().length > 0) return true;
                if (el.hasAttribute('aria-label') && el.getAttribute('aria-label').trim().length > 0) return true;
                if (el.hasAttribute('aria-labelledby')) return true;
                if (el.hasAttribute('title') && el.getAttribute('title').trim().length > 0) return true;
                
                const imgs = el.querySelectorAll('img');
                for (let img of imgs) {
                    if (img.hasAttribute('alt') && img.getAttribute('alt').trim().length > 0) return true;
                }
                return false;
            }""")
            
            if not has_discernible_text:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content, aria-label, or an image with non-empty alt text"
                })
        return violations

class EmptyButtonsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="empty-buttons",
            description="Buttons must have discernible text",
            wcag_criterion="4.1.2",
            level="A",
            impact="critical",
            applicability="button"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("button").all()
        for loc in locators:
            has_discernible_text = loc.evaluate("""el => {
                if (el.textContent.trim().length > 0) return true;
                if (el.hasAttribute('aria-label') && el.getAttribute('aria-label').trim().length > 0) return true;
                if (el.hasAttribute('aria-labelledby')) return true;
                if (el.hasAttribute('title') && el.getAttribute('title').trim().length > 0) return true;
                if (el.hasAttribute('value') && el.getAttribute('value').trim().length > 0) return true;
                return false;
            }""")
            
            if not has_discernible_text:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Button has no discernible text",
                    "suggestion": "Add text content, aria-label, or value attribute"
                })
        return violations

class MissingTitleRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="missing-title",
            description="Page must have a title element",
            wcag_criterion="2.4.2",
            level="A",
            impact="serious",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        title = page.title()
        if not title or not title.strip():
            return [{
                "element": "<head>",
                "message": "Page missing title element or title is empty",
                "suggestion": "Add a descriptive <title> element in the <head>"
            }]
        return []

class AutofocusInputsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="autofocus-inputs",
            description="Inputs should not have autofocus",
            wcag_criterion="2.4.3",
            level="A",
            impact="minor",
            applicability="form"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("[autofocus]").all()
        for loc in locators:
            html_snippet = loc.evaluate("el => el.outerHTML")
            violations.append({
                "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                "message": "Element has autofocus attribute",
                "suggestion": "Remove autofocus to avoid disorienting users"
            })
        return violations

class MissingAltTextRule(AbstractRule):
    """DEPRECATED: Use ComplexAltTextRule from perceivable_rules instead.
    Maintained for backward compatibility for external consumers."""
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="missing-alt",
            description="Images must have alternate text",
            wcag_criterion="1.1.1",
            level="A",
            impact="critical",
            applicability="image"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        # Proxy to the new rule
        from .perceivable_rules import ComplexAltTextRule
        return ComplexAltTextRule().evaluate(page)

def get_core_rules() -> List[AbstractRule]:
    return [
        MissingLabelsRule(),
        MissingLangRule(),
        EmptyLinksRule(),
        EmptyButtonsRule(),
        MissingTitleRule(),
        AutofocusInputsRule(),
        ComplexAltTextRule(),
        TimeBasedMediaRule(),
        AdaptableLandmarksRule(),
        AdaptableReadingSeqRule(),
        # ContrastMinimumRule(), # TODO: Stubbed out pending proper contrast calculation library
        FocusAppearanceRule(),
        KeyboardAccessibilityRule(),
        NavigableRule(),
        TargetSizeRule(),
        InputAssistanceRule(),
        IdentifyInputPurposeRule(),
        ARIAValidationRule(),
        StatusMessagesRule()
    ]
