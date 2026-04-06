from typing import List, Dict, Any
from playwright.sync_api import Page
from . import AbstractRule, RuleMetadata

class ARIAValidationRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="aria-validation",
            description="ARIA roles must be used with valid states and properties",
            wcag_criterion="4.1.2",
            level="A",
            impact="critical",
            applicability="aria"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("[role]").all()
        for loc in locators:
            role = loc.get_attribute("role")
            
            # Simple heuristic example: role="combobox" requires aria-expanded and aria-controls
            if role == "combobox":
                has_expanded = loc.get_attribute("aria-expanded") is not None
                has_controls = loc.get_attribute("aria-controls") is not None
                if not has_expanded or not has_controls:
                    html_snippet = loc.evaluate("el => el.outerHTML")
                    violations.append({
                        "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                        "message": "Combobox pattern is missing a required attribute (needs both aria-expanded and aria-controls)",
                        "suggestion": "Add missing attributes to fulfill compatible widget state requirements"
                    })
                    
            # role="checked" is not valid, commonly typo'd. 
            if role == "checked":
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": f"Invalid ARIA role: {role}",
                    "suggestion": "Use a valid ARIA role (e.g., checkbox) and aria-checked attribute"
                })
        return violations

class StatusMessagesRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="status-messages",
            description="Status messages must be programmatically determinable through role or properties",
            wcag_criterion="4.1.3",
            level="AA",
            impact="moderate",
            applicability="page"
        )
    
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        # Look for typical alert blocks. 
        # NOTE: This relies on class-name heuristics (.alert, .error, .success, .toast). 
        # This is fragile, framework-dependent, and may cause false positives on
        # non-status elements using these classes, while missing others.
        locators = page.locator(".alert, .error, .success, .toast").all()
        for loc in locators:
            has_role = loc.evaluate("el => el.hasAttribute('role') && ['alert', 'status', 'log'].includes(el.getAttribute('role'))")
            has_live = loc.get_attribute("aria-live") is not None
            
            if not has_role and not has_live:
                html_snippet = loc.evaluate("el => el.outerHTML")
                violations.append({
                    "element": html_snippet[:100] + "..." if len(html_snippet) > 100 else html_snippet,
                    "message": "Potential status message is not exposed to assistive tech",
                    "suggestion": "Add role='alert' or aria-live='polite' to dynamic message containers"
                })
        return violations
