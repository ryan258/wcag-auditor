from typing import List, Dict, Any
from playwright.sync_api import Page
from . import AbstractRule, RuleMetadata

class InputAssistanceRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="input-assistance-error-msg",
            description="If an input error is automatically detected, it must be described to the user in text",
            wcag_criterion="3.3.1",
            level="A",
            impact="serious",
            applicability="form"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("[aria-invalid='true']").all()
        for loc in locators:
            has_errormessage = loc.get_attribute("aria-errormessage") is not None
            has_describedby = loc.get_attribute("aria-describedby") is not None
            
            if not has_errormessage and not has_describedby:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Input marked as invalid lacks an associated error message",
                    "suggestion": "Add an aria-errormessage or aria-describedby attribute pointing to the error text"
                })
        return violations

class IdentifyInputPurposeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="identify-input-purpose",
            description="The purpose of fields collecting user information can be programmatically determined (e.g. autocomplete)",
            wcag_criterion="1.3.5",
            level="AA",
            impact="moderate",
            applicability="form"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        # Finding redundant entry inherently requires multi-page context, but we can do a heuristic 
        # looking for identical name/id patterns across long forms missing autocomplete
        locators = page.locator("input[type='text'], input[type='email'], input[type='tel']").all()
        for loc in locators:
            name = loc.get_attribute("name")
            autocomplete = loc.get_attribute("autocomplete")
            
            # Common repeatable fields like shipping address, billing address
            if name and any(keyword in name.lower() for keyword in ["address", "phone", "email", "name"]):
                if not autocomplete:
                    html_snippet = loc.evaluate("el => el.outerHTML")
                    violations.append({
                        "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                        "message": f"Common input field '{name}' is missing an autocomplete attribute",
                        "suggestion": "Add an appropriate autocomplete attribute to prevent redundant entry across sessions"
                    })
        return violations
