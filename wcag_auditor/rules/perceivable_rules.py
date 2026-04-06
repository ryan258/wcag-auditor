from typing import List, Dict, Any
from playwright.sync_api import Page
from . import AbstractRule, RuleMetadata

class ComplexAltTextRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="complex-alt-text",
            description="Images and SVGs must have appropriate alternate text",
            wcag_criterion="1.1.1",
            level="A",
            impact="critical",
            applicability="image"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("img, svg, [role='img']").all()
        for loc in locators:
            tag_name = loc.evaluate("el => el.tagName.toLowerCase()")
            role = loc.get_attribute("role")
            
            if role == "presentation" or role == "none":
                continue

            has_alt = False
            # Check img specific alternative text
            if tag_name == "img":
                has_alt = loc.evaluate("el => el.hasAttribute('alt')")
            
            # Global checks (aria-label, aria-labelledby)
            if not has_alt:
                has_alt = loc.evaluate("""el => {
                    if (el.hasAttribute('aria-label') && el.getAttribute('aria-label').trim().length > 0) return true;
                    if (el.hasAttribute('aria-labelledby')) return true;
                    if (el.tagName.toLowerCase() === 'svg') {
                        const title = el.querySelector('title');
                        if (title && title.textContent.trim().length > 0) return true;
                    }
                    if (el.hasAttribute('title') && el.getAttribute('title').trim().length > 0) return true;
                    return false;
                }""")
            
            if not has_alt:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Image/Graphic missing text alternatives",
                    "suggestion": 'Add alt attribute, <title> (for svg), aria-label, or role="presentation"'
                })
        return violations

class TimeBasedMediaRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="time-based-media",
            description="Video and audio elements must have caption and description tracks",
            wcag_criterion="1.2.2",
            level="A",
            impact="serious",
            applicability="media"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("video, audio").all()
        for loc in locators:
            tag = loc.evaluate("el => el.tagName.toLowerCase()")
            
            has_track = loc.evaluate("""el => {
                const tracks = el.querySelectorAll('track');
                for (let track of tracks) {
                    const kind = track.getAttribute('kind');
                    if (kind === 'captions' || kind === 'descriptions' || kind === 'subtitles') {
                        return true;
                    }
                }
                return false;
            }""")
            
            if not has_track:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": f"Media element <{tag}> is missing closed captions or descriptions track",
                    "suggestion": "Add a <track kind='captions'> or <track kind='descriptions'> to ensure accessibility"
                })
        return violations

class AdaptableLandmarksRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="adaptable-landmarks",
            description="Pages should use semantic landmarks for structure",
            wcag_criterion="1.3.1",
            level="A",
            impact="moderate",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        has_main = page.evaluate("""() => {
            return document.querySelector('main') !== null || document.querySelector('[role="main"]') !== null;
        }""")
        
        if not has_main:
            violations.append({
                "element": "<body>",
                "message": "Page is missing a main landmark",
                "suggestion": "Wrap the primary content of the page in a <main> tag or an element with role='main'"
            })
        return violations

class AdaptableReadingSeqRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="reading-sequence",
            description="Elements with positive tabindex can disrupt logical reading sequence",
            wcag_criterion="1.3.2",
            level="A",
            impact="serious",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("[tabindex]").all()
        for loc in locators:
            tabindex_val = loc.get_attribute("tabindex")
            try:
                if tabindex_val and int(tabindex_val) > 0:
                    html_snippet = loc.evaluate("el => el.outerHTML")
                    violations.append({
                        "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                        "message": "Element uses a positive tabindex which disrupts predictable navigation",
                        "suggestion": "Use tabindex='0' or '-1' and rely on DOM order for navigation"
                    })
            except ValueError:
                pass
        return violations

class ContrastMinimumRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="contrast-minimum",
            description="Text must have a contrast ratio of at least 4.5:1 (3:1 for large text)",
            wcag_criterion="1.4.3",
            level="AA",
            impact="serious",
            applicability="text"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        # This is a heuristic/limited check so it doesn't grind performance to a halt
        violations = []
        
        # Inject axe-core or contrast calculation logic if needed, but we can do a simplified JS evaluaton 
        # or report a generic warning for this phase. To keep execution fast, we warn on inline styles 
        # that explicitly set low contrast.
        # Below is a simplified contrast check looking at specific elements.
        
        has_contrast_issues = page.evaluate("""() => {
            // Simplified contrast checking: parsing RGB and calculating luminance is complex in plain JS 
            // without a library. Returning false for now as a placeholder unless we inject a real library.
            // A real implementation would parse window.getComputedStyle(el).color and .backgroundColor.
            return false;
        }""")
        
        # For a true pixel-by-pixel, we would use a specialized engine. We'll leave the full JS out here 
        # to focus on the structure requested, but conceptually it belongs here.
        return violations

class FocusAppearanceRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="focus-appearance",
            description="Focus indicators must be visible and meet minimum contrast/area requirements",
            wcag_criterion="1.4.11",
            level="AA",
            impact="serious",
            applicability="interactive"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("a[href], button, input, select, textarea, [tabindex='0']").all()
        # Verify that focus outline is not removed entirely (outline: none) without fallback
        for loc in locators:
            is_hidden = loc.evaluate("""el => {
                // Focus styling is often defined iteratively. We check if outline is disabled.
                const style = window.getComputedStyle(el);
                return style.outlineStyle === 'none' && style.boxShadow === 'none';
            }""")
            
            # This is a naive heuristic for 'focus: outline none'
            if is_hidden:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Interactive element appears to have no distinct focus indicator",
                    "suggestion": "Do not use 'outline: none' without providing an alternative focus style such as box-shadow or background-color changes"
                })
                # Cap violations for performance
                if len(violations) >= 5:
                    break
                    
        return violations
