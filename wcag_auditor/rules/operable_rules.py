from typing import List, Dict, Any
from playwright.sync_api import Page
from . import AbstractRule, RuleMetadata

class KeyboardAccessibilityRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="keyboard-accessibility",
            description="All functionality must be available from a keyboard",
            wcag_criterion="2.1.1",
            level="A",
            impact="critical",
            applicability="interactive"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator(r"[onclick], [ng-click], [v-on\:click]").all()
        for loc in locators:
            tag = loc.evaluate("el => el.tagName.toLowerCase()")
            if tag not in ["button", "a", "input", "select", "textarea"]:
                has_key_handler = loc.evaluate("el => el.hasAttribute('onkeydown') || el.hasAttribute('onkeyup') || el.hasAttribute('onkeypress')")
                tabindex = loc.get_attribute("tabindex")
                
                if not has_key_handler and tabindex is None:
                    html_snippet = loc.evaluate("el => el.outerHTML")
                    violations.append({
                        "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                        "message": "Custom interactive element lacks keyboard event handlers or tabindex",
                        "suggestion": "Add tabindex='0' and equivalent onkeydown handlers for click events"
                    })
        return violations

class NavigableRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="navigable-skip-links",
            description="A mechanism must be available to bypass blocks of content",
            wcag_criterion="2.4.1",
            level="A",
            impact="moderate",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        # Check for skip link
        has_skip_link = page.evaluate("""() => {
            const links = Array.from(document.links);
            return links.some(l => 
                l.getAttribute('href') && 
                l.getAttribute('href').startsWith('#') &&
                (l.textContent.toLowerCase().includes('skip') || l.getAttribute('aria-label')?.toLowerCase().includes('skip'))
            );
        }""")
        
        if not has_skip_link:
            violations.append({
                "element": "<body>",
                "message": "Page is missing a 'Skip to Content' link",
                "suggestion": "Add a hidden skip link at the top of the body referencing the main content ID"
            })
            
        # Check iframes for titles (2.4.1 contextual navigable element)
        iframes = page.locator("iframe").all()
        for iframe in iframes:
            if not iframe.get_attribute("title"):
                html_snippet = iframe.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Iframe missing title attribute",
                    "suggestion": "Add a descriptive title attribute to the iframe"
                })
                
        return violations

class TargetSizeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="target-size-minimum",
            description="Target size for pointer inputs must be at least 24x24 CSS pixels",
            wcag_criterion="2.5.8",
            level="AA",
            impact="serious",
            applicability="interactive"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("button, a[href], input[type='button'], input[type='submit']").all()
        for loc in locators:
            box = loc.bounding_box()
            if box:
                width = box["width"]
                height = box["height"]
                if width < 24 or height < 24:
                    html_snippet = loc.evaluate("el => el.outerHTML")
                    violations.append({
                        "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                        "message": f"Interactive element target size ({width}x{height}) is less than 24x24",
                        "suggestion": "Increase min-width and min-height, or add padding to expand the clickable area"
                    })
        return violations
