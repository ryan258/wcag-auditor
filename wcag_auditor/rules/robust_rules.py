from typing import Any, Dict, List

from playwright.sync_api import Page

from . import AbstractRule, RuleMetadata
from .helpers import build_finding, locator_html

VALID_ARIA_ROLES = {
    "alert",
    "alertdialog",
    "application",
    "article",
    "banner",
    "blockquote",
    "button",
    "caption",
    "cell",
    "checkbox",
    "code",
    "columnheader",
    "combobox",
    "complementary",
    "contentinfo",
    "definition",
    "deletion",
    "dialog",
    "directory",
    "document",
    "emphasis",
    "feed",
    "figure",
    "form",
    "generic",
    "grid",
    "gridcell",
    "group",
    "heading",
    "img",
    "insertion",
    "link",
    "list",
    "listbox",
    "listitem",
    "log",
    "main",
    "mark",
    "marquee",
    "math",
    "menu",
    "menubar",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "meter",
    "navigation",
    "none",
    "note",
    "option",
    "paragraph",
    "presentation",
    "progressbar",
    "radio",
    "radiogroup",
    "region",
    "row",
    "rowgroup",
    "rowheader",
    "scrollbar",
    "search",
    "searchbox",
    "separator",
    "slider",
    "spinbutton",
    "status",
    "strong",
    "subscript",
    "superscript",
    "switch",
    "tab",
    "table",
    "tablist",
    "tabpanel",
    "term",
    "textbox",
    "time",
    "timer",
    "toolbar",
    "tooltip",
    "tree",
    "treegrid",
    "treeitem",
}

ROLE_REQUIRED_ATTRIBUTES = {
    "checkbox": {"aria-checked"},
    "combobox": {"aria-expanded", "aria-controls"},
    "heading": {"aria-level"},
    "menuitemcheckbox": {"aria-checked"},
    "menuitemradio": {"aria-checked"},
    "option": {"aria-selected"},
    "progressbar": {"aria-valuenow"},
    "radio": {"aria-checked"},
    "scrollbar": {"aria-controls", "aria-valuemin", "aria-valuemax", "aria-valuenow"},
    "slider": {"aria-valuemin", "aria-valuemax", "aria-valuenow"},
    "spinbutton": {"aria-valuemin", "aria-valuemax", "aria-valuenow"},
    "switch": {"aria-checked"},
    "tab": {"aria-selected"},
    "tabpanel": {"aria-labelledby"},
}

BOOLEAN_ATTRIBUTES = {
    "aria-atomic",
    "aria-busy",
    "aria-disabled",
    "aria-expanded",
    "aria-hidden",
    "aria-modal",
    "aria-multiline",
    "aria-multiselectable",
    "aria-readonly",
    "aria-required",
    "aria-selected",
}

TRISTATE_ATTRIBUTES = {"aria-checked", "aria-pressed"}
NUMERIC_ATTRIBUTES = {"aria-level", "aria-valuemin", "aria-valuemax", "aria-valuenow"}
IDREF_ATTRIBUTES = {
    "aria-activedescendant",
    "aria-controls",
    "aria-describedby",
    "aria-details",
    "aria-errormessage",
    "aria-flowto",
    "aria-labelledby",
    "aria-owns",
}
TOKEN_ATTRIBUTES = {
    "aria-current": {"page", "step", "location", "date", "time", "true", "false"},
    "aria-haspopup": {"false", "true", "menu", "listbox", "tree", "grid", "dialog"},
    "aria-invalid": {"false", "true", "grammar", "spelling"},
    "aria-live": {"off", "polite", "assertive"},
    "aria-orientation": {"horizontal", "vertical"},
    "aria-sort": {"none", "ascending", "descending", "other"},
}
ARIA_ATTRIBUTE_SELECTOR = ",".join(
    ["[role]"]
    + [
        f"[{attr}]"
        for attr in sorted(
            BOOLEAN_ATTRIBUTES
            | TRISTATE_ATTRIBUTES
            | NUMERIC_ATTRIBUTES
            | IDREF_ATTRIBUTES
            | set(TOKEN_ATTRIBUTES)
        )
    ]
)


class ARIAValidationRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="aria-validation",
            description="ARIA roles, states, and properties must be valid and internally consistent",
            wcag_criterion="4.1.2",
            level="A",
            impact="critical",
            applicability="aria",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        for loc in page.locator(ARIA_ATTRIBUTE_SELECTOR).all():
            role = (loc.get_attribute("role") or "").strip()
            html = locator_html(loc)

            if role and role not in VALID_ARIA_ROLES:
                violations.append(
                    build_finding(
                        element=html,
                        message=f"Invalid ARIA role: {role}",
                        suggestion="Use a valid ARIA role that matches the widget or landmark behavior.",
                        remediation_code='<div role="checkbox" aria-checked="false"></div>',
                    )
                )
                continue

            required_attrs = ROLE_REQUIRED_ATTRIBUTES.get(role, set())
            missing_attrs = sorted(
                attr for attr in required_attrs if loc.get_attribute(attr) is None
            )
            if missing_attrs:
                violations.append(
                    build_finding(
                        element=html,
                        message=f"Role '{role}' is missing required ARIA attributes: {', '.join(missing_attrs)}",
                        suggestion="Add the required ARIA states and relationships for the selected widget pattern.",
                    )
                )

            for attr in BOOLEAN_ATTRIBUTES:
                value = loc.get_attribute(attr)
                if value is not None and value not in {"true", "false"}:
                    violations.append(
                        build_finding(
                            element=html,
                            message=f"{attr} must be 'true' or 'false', not '{value}'",
                            suggestion="Use a valid boolean value for the ARIA attribute.",
                        )
                    )

            for attr in TRISTATE_ATTRIBUTES:
                value = loc.get_attribute(attr)
                if value is not None and value not in {"true", "false", "mixed"}:
                    violations.append(
                        build_finding(
                            element=html,
                            message=f"{attr} must be 'true', 'false', or 'mixed', not '{value}'",
                            suggestion="Use a valid ARIA tristate value.",
                        )
                    )

            for attr, valid_tokens in TOKEN_ATTRIBUTES.items():
                value = loc.get_attribute(attr)
                if value is not None and value not in valid_tokens:
                    violations.append(
                        build_finding(
                            element=html,
                            message=f"{attr} has invalid value '{value}'",
                            suggestion=f"Use one of: {', '.join(sorted(valid_tokens))}.",
                        )
                    )

            for attr in NUMERIC_ATTRIBUTES:
                value = loc.get_attribute(attr)
                if value is None or attr == "aria-valuetext":
                    continue
                try:
                    numeric_value = float(value)
                except ValueError:
                    violations.append(
                        build_finding(
                            element=html,
                            message=f"{attr} must be numeric, not '{value}'",
                            suggestion="Provide a numeric value for the ARIA attribute.",
                        )
                    )
                    continue
                if attr == "aria-level" and numeric_value <= 0:
                    violations.append(
                        build_finding(
                            element=html,
                            message="aria-level must be greater than zero",
                            suggestion="Use a positive integer that matches the heading level.",
                        )
                    )

            for attr in IDREF_ATTRIBUTES:
                raw_value = loc.get_attribute(attr)
                if not raw_value:
                    continue
                missing_ids = loc.evaluate(
                    """(el, attribute) => {
                        const ids = (el.getAttribute(attribute) || '').split(/\\s+/).filter(Boolean);
                        return ids.filter(id => !document.getElementById(id));
                    }""",
                    attr,
                )
                if missing_ids:
                    violations.append(
                        build_finding(
                            element=html,
                            message=f"{attr} references missing element ids: {', '.join(missing_ids)}",
                            suggestion="Ensure ARIA IDREF attributes point at existing elements in the DOM.",
                        )
                    )

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
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate("""() => {
                const selectors = '.alert, .error, .success, .toast, .snackbar, .notification, [data-status-message]';
                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        const role = (el.getAttribute('role') || '').trim();
                        const live = (el.getAttribute('aria-live') || '').trim();
                        if (['alert', 'status', 'log'].includes(role) || ['polite', 'assertive'].includes(live)) {
                            return [];
                        }

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Potential status message is not exposed to assistive technology',
                            suggestion: "Add role='status', role='alert', role='log', or an appropriate aria-live value.",
                            remediation_code: '<div class="toast" role="status" aria-live="polite">Saved</div>',
                        }];
                    });
            }""")
