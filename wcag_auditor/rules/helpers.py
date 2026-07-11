"""Shared helpers for rule implementations."""

import re
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
    if locator.count() == 0:
        return "Unknown"
    return truncate_html(locator.evaluate("el => el.outerHTML"), limit=limit)


def selector_for_html_snippet(page: Page, element: Any) -> Optional[str]:
    """Return a CSS selector when an HTML excerpt identifies exactly one element."""
    if not isinstance(element, str) or not element.lstrip().startswith("<"):
        return None

    try:
        return page.evaluate(
            """snippet => {
                const truncated = snippet.endsWith('...');
                const prefix = truncated ? snippet.slice(0, -3) : snippet;
                const matches = Array.from(document.querySelectorAll('*')).filter(el =>
                    truncated ? el.outerHTML.startsWith(prefix) : el.outerHTML === prefix
                );
                if (matches.length !== 1) return null;

                const element = matches[0];
                const unique = selector => {
                    try { return document.querySelectorAll(selector).length === 1; }
                    catch (_) { return false; }
                };
                for (const attribute of ['data-testid', 'data-test-id', 'data-test', 'data-qa']) {
                    const value = element.getAttribute(attribute);
                    if (value) {
                        const selector = `[${attribute}="${CSS.escape(value)}"]`;
                        if (unique(selector)) return selector;
                    }
                }
                if (element.id) {
                    const selector = `#${CSS.escape(element.id)}`;
                    if (unique(selector)) return selector;
                }

                const path = [];
                for (let current = element; current && current.nodeType === Node.ELEMENT_NODE; current = current.parentElement) {
                    let segment = current.tagName.toLowerCase();
                    const siblings = Array.from(current.parentElement?.children || []).filter(
                        sibling => sibling.tagName === current.tagName
                    );
                    if (siblings.length > 1) segment += `:nth-of-type(${siblings.indexOf(current) + 1})`;
                    path.unshift(segment);
                }
                const selector = path.join(' > ');
                return unique(selector) ? selector : null;
            }""",
            element,
        )
    except Exception:
        return None


def parse_aria_snapshot(snapshot: str) -> tuple[Optional[str], Optional[str]]:
    """Parse role and accessible name from Playwright locator.aria_snapshot()."""
    if not snapshot:
        return None, None
    first_line = snapshot.split('\n')[0].strip()
    match = re.match(r'^-\s+([a-zA-Z0-9_-]+)\s+"([^"]*)"(?::|\s|$)', first_line)
    if match:
        return match.group(1), match.group(2)
    match = re.match(r'^-\s+([a-zA-Z0-9_-]+)(?::\s+(.*))?$', first_line)
    if match:
        role = match.group(1)
        name = match.group(2) if match.group(2) else None
        if role == 'text' and name:
            return None, name
        return role, None
    return None, None


def describe_element(locator: Locator, page: Page) -> Dict[str, Any]:
    """Resolve element identity details (selector, accessible name, role, coordinates, frame context)."""
    if not locator or locator.count() == 0:
        return {
            "element": "Unknown",
            "selector": "Unknown",
            "accessible_name": None,
            "role": None,
            "bounding_box": None,
            "frame_context": None
        }

    try:
        # Get element properties via JS evaluation
        info = locator.evaluate(
            """el => {
                const getStableSelector = (element) => {
                    const testIdAttrs = ['data-testid', 'data-test-id', 'data-test', 'data-qa'];

                    const isUnique = (sel) => {
                        try {
                            return document.querySelectorAll(sel).length === 1;
                        } catch (e) {
                            return false;
                        }
                    };

                    for (const attr of testIdAttrs) {
                        if (element.hasAttribute(attr)) {
                            const val = element.getAttribute(attr);
                            if (val) {
                                const sel = `[${attr}="${CSS.escape(val)}"]`;
                                if (isUnique(sel)) return sel;
                            }
                        }
                    }

                    if (element.id) {
                        const sel = `#${CSS.escape(element.id)}`;
                        if (isUnique(sel)) return sel;
                    }

                    const path = [];
                    let current = element;
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        let tag = current.tagName.toLowerCase();
                        let hasUniqueAttr = false;

                        for (const attr of testIdAttrs) {
                            if (current.hasAttribute(attr)) {
                                const val = current.getAttribute(attr);
                                if (val) {
                                    tag += `[${attr}="${CSS.escape(val)}"]`;
                                    hasUniqueAttr = true;
                                    break;
                                }
                            }
                        }

                        if (!hasUniqueAttr && current.id) {
                            tag += `#${CSS.escape(current.id)}`;
                            hasUniqueAttr = true;
                        }

                        if (hasUniqueAttr) {
                            path.unshift(tag);
                            const fullSel = path.join(' > ');
                            if (isUnique(fullSel)) {
                                return fullSel;
                            }
                        } else {
                            let sibling = current;
                            let nth = 1;
                            while (sibling.previousElementSibling) {
                                sibling = sibling.previousElementSibling;
                                if (sibling.tagName === current.tagName) {
                                    nth++;
                                }
                            }

                            let hasSameTagSiblings = false;
                            let sib = current.nextElementSibling;
                            while (sib) {
                                if (sib.tagName === current.tagName) {
                                    hasSameTagSiblings = true;
                                    break;
                                }
                                sib = sib.nextElementSibling;
                            }
                            sib = current.previousElementSibling;
                            while (sib) {
                                if (sib.tagName === current.tagName) {
                                    hasSameTagSiblings = true;
                                    break;
                                }
                                sib = sib.previousElementSibling;
                            }

                            if (hasSameTagSiblings) {
                                tag += `:nth-of-type(${nth})`;
                            }
                            path.unshift(tag);
                        }
                        current = current.parentElement;
                    }
                    return path.join(' > ');
                };

                let frameContext = null;
                const currentWindow = el.ownerDocument.defaultView;
                if (currentWindow !== window) {
                    try {
                        const frameEl = currentWindow.frameElement;
                        if (frameEl) {
                            frameContext = {
                                tagName: frameEl.tagName.toLowerCase(),
                                src: frameEl.getAttribute('src') || '',
                                id: frameEl.id || '',
                                name: frameEl.name || ''
                            };
                        }
                    } catch (e) {
                        frameContext = { crossOrigin: true };
                    }
                }

                return {
                    outerHTML: el.outerHTML,
                    stableSelector: getStableSelector(el),
                    frameContext: frameContext
                };
            }"""
        )
    except Exception:
        info = {
            "outerHTML": "Unknown",
            "stableSelector": "Unknown",
            "frameContext": None
        }

    # Bounding Box
    bounding_box = None
    try:
        box = locator.bounding_box()
        if box:
            bounding_box = {
                "x": box["x"],
                "y": box["y"],
                "width": box["width"],
                "height": box["height"]
            }
    except Exception:
        pass

    # Accessible Name and Role via ARIA Snapshot
    role, name = None, None
    try:
        snapshot = locator.aria_snapshot()
        if snapshot:
            role, name = parse_aria_snapshot(snapshot)
    except Exception:
        pass

    # Determine final selector (prefer semantic role/name hint if unique)
    selector = info.get("stableSelector", "Unknown")
    if role and name and selector and not selector.startswith("#") and not any(k in selector for k in ["data-testid", "data-test-id", "data-test", "data-qa"]):
        escaped_name = name.replace('"', '\\"')
        semantic_sel = f'role={role}[name="{escaped_name}"]'
        try:
            if page.locator(semantic_sel).count() == 1:
                selector = semantic_sel
        except Exception:
            pass

    return {
        "element": truncate_html(info.get("outerHTML") or "Unknown"),
        "selector": selector,
        "accessible_name": name,
        "role": role,
        "bounding_box": bounding_box,
        "frame_context": info.get("frameContext")
    }


def build_finding(
    *,
    element: str,
    message: str,
    suggestion: str,
    finding_type: str = "violation",
    remediation_code: Optional[str] = None,
    locator: Optional[Locator] = None,
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
    if locator is not None:
        finding["locator"] = locator
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
