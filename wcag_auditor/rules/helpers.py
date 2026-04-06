"""Shared helpers for rule implementations."""

from typing import Any, Dict, List, Optional

from playwright.sync_api import Locator, Page


FOCUSABLE_SELECTOR = (
    "a[href], button, input:not([type='hidden']), select, textarea, summary, "
    "iframe, [tabindex]:not([tabindex='-1'])"
)


def truncate_html(html: str, limit: int = 140) -> str:
    """Return a stable, shortened HTML snippet for report output."""
    if len(html) <= limit:
        return html
    return f"{html[:limit]}..."


def locator_html(locator: Locator, limit: int = 140) -> str:
    """Capture a locator's outer HTML as a report snippet."""
    return truncate_html(locator.evaluate("el => el.outerHTML"), limit=limit)


def build_finding(
    *,
    element: str,
    message: str,
    suggestion: str,
    finding_type: str = "violation",
    remediation_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a normalized finding payload for the auditor pipeline."""
    finding: Dict[str, Any] = {
        "element": element,
        "message": message,
        "suggestion": suggestion,
    }
    if finding_type != "violation":
        finding["finding_type"] = finding_type
    if remediation_code:
        finding["remediation_code"] = remediation_code
    return finding


def collect_focus_indicator_findings(
    page: Page,
    *,
    message: str,
    suggestion: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Heuristically detect interactive elements that lack visible focus styles."""
    findings: List[Dict[str, Any]] = []
    locators = page.locator(FOCUSABLE_SELECTOR).all()

    for loc in locators:
        is_visible = loc.evaluate(
            """el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.display !== 'none' &&
                    style.visibility !== 'hidden'
                );
            }"""
        )
        if not is_visible:
            continue

        page.evaluate("document.activeElement?.blur()")
        before_style = loc.evaluate(
            """el => {
                const style = window.getComputedStyle(el);
                return {
                    outlineStyle: style.outlineStyle,
                    outlineWidth: style.outlineWidth,
                    boxShadow: style.boxShadow,
                    backgroundColor: style.backgroundColor,
                    borderTopColor: style.borderTopColor,
                    borderRightColor: style.borderRightColor,
                    borderBottomColor: style.borderBottomColor,
                    borderLeftColor: style.borderLeftColor,
                    borderTopWidth: style.borderTopWidth,
                    borderRightWidth: style.borderRightWidth,
                    borderBottomWidth: style.borderBottomWidth,
                    borderLeftWidth: style.borderLeftWidth
                };
            }"""
        )
        focused_style = loc.evaluate(
            """el => {
                el.focus({preventScroll: true, focusVisible: true});
                const style = window.getComputedStyle(el);
                return {
                    outlineStyle: style.outlineStyle,
                    outlineWidth: style.outlineWidth,
                    boxShadow: style.boxShadow,
                    backgroundColor: style.backgroundColor,
                    borderTopColor: style.borderTopColor,
                    borderRightColor: style.borderRightColor,
                    borderBottomColor: style.borderBottomColor,
                    borderLeftColor: style.borderLeftColor,
                    borderTopWidth: style.borderTopWidth,
                    borderRightWidth: style.borderRightWidth,
                    borderBottomWidth: style.borderBottomWidth,
                    borderLeftWidth: style.borderLeftWidth,
                    focused: document.activeElement === el
                };
            }"""
        )

        has_outline = (
            focused_style["outlineStyle"] != "none"
            and focused_style["outlineWidth"] != "0px"
        )
        has_box_shadow = focused_style["boxShadow"] != "none"
        has_background_change = (
            focused_style["backgroundColor"] != before_style["backgroundColor"]
        )
        has_border_change = any(
            focused_style[key] != before_style[key]
            for key in [
                "borderTopColor",
                "borderRightColor",
                "borderBottomColor",
                "borderLeftColor",
                "borderTopWidth",
                "borderRightWidth",
                "borderBottomWidth",
                "borderLeftWidth",
            ]
        )
        has_visible_indicator = (
            focused_style["focused"]
            and (has_outline or has_box_shadow or has_background_change or has_border_change)
        )

        page.evaluate("document.activeElement?.blur()")

        if not has_visible_indicator:
            findings.append(
                build_finding(
                    element=locator_html(loc),
                    message=message,
                    suggestion=suggestion,
                    remediation_code=(
                        ":focus-visible {\n"
                        "  outline: 3px solid #005fcc;\n"
                        "  outline-offset: 2px;\n"
                        "}"
                    ),
                )
            )
            if len(findings) >= limit:
                break

    return findings
