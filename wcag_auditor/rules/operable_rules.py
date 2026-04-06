from typing import Any, Dict, List, Set

from playwright.sync_api import Page

from . import AbstractRule, RuleMetadata
from .helpers import build_finding, locator_html


class KeyboardAccessibilityRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="keyboard-accessibility",
            description="All functionality must be available from a keyboard",
            wcag_criterion="2.1.1",
            level="A",
            impact="critical",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        for loc in page.locator(r"[onclick], [ng-click], [v-on\:click]").all():
            tag = loc.evaluate("el => el.tagName.toLowerCase()")
            if tag in ["button", "a", "input", "select", "textarea"]:
                continue

            has_key_handler = loc.evaluate(
                "el => el.hasAttribute('onkeydown') || el.hasAttribute('onkeyup') || el.hasAttribute('onkeypress')"
            )
            tabindex = loc.get_attribute("tabindex")

            if not has_key_handler and tabindex is None:
                violations.append(
                    build_finding(
                        element=locator_html(loc),
                        message="Custom interactive element lacks keyboard event handlers or tabindex",
                        suggestion="Add tabindex='0' and keyboard handlers that mirror the click behavior.",
                        remediation_code=(
                            '<div tabindex="0" onkeydown="if (event.key === \'Enter\' || event.key === \' \') activate()">'
                            "\n  Interactive content\n</div>"
                        ),
                    )
                )
        return violations


class KeyboardTrapRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="keyboard-trap",
            description="Components should provide an obvious keyboard escape path",
            wcag_criterion="2.1.2",
            level="A",
            impact="critical",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const selectors = 'dialog, [role="dialog"], [aria-modal="true"], [role="menu"], [role="listbox"]';
                const focusable = 'a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])';

                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        if (!el.querySelector(focusable)) return [];

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        const snippet = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                        const closeControl = el.querySelector(
                            '[aria-label*="close" i], [data-dismiss], [data-close], button.close, [data-testid*="close"]'
                        );
                        const escapeScript = [
                            el.getAttribute('onkeydown') || '',
                            document.body?.getAttribute('onkeydown') || '',
                            document.documentElement?.getAttribute('onkeydown') || '',
                        ].join(' ').toLowerCase();

                        if (closeControl || escapeScript.includes('escape') || escapeScript.includes('esc')) {
                            return [];
                        }

                        return [{
                            element: snippet,
                            message: 'Potential keyboard trap: dialog-like component has focusable content but no detectable close or escape mechanism',
                            suggestion: 'Provide a keyboard-operable close button and support closing the component with Escape.',
                            finding_type: 'needs_review',
                            remediation_code: '<button type="button" aria-label="Close dialog">Close</button>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class EnoughTimeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="enough-time-controls",
            description="Auto-updating content should provide pause, stop, or resume controls",
            wcag_criterion="2.2.2",
            level="A",
            impact="serious",
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const selectors = [
                    'marquee', '[aria-live]', '[role="timer"]', '[data-carousel]', '[data-auto-rotate]',
                    '.carousel', '.slider', '.ticker', '[autoplay]'
                ].join(',');
                const pausePattern = /pause|stop|resume|play/i;

                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        const container = el.closest('section, article, form, main, aside, div') || el.parentElement || el;
                        const controls = Array.from(container.querySelectorAll('button, a[href], input[type="button"], input[type="submit"]'));
                        const hasControl = controls.some(control => {
                            const label = (
                                control.textContent ||
                                control.getAttribute('aria-label') ||
                                control.getAttribute('title') ||
                                control.value ||
                                ''
                            ).trim();
                            return pausePattern.test(label);
                        });

                        if (hasControl) return [];

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        const snippet = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                        return [{
                            element: snippet,
                            message: 'Auto-updating content appears without a pause, stop, or resume control',
                            suggestion: 'Expose controls that let users pause or stop moving, blinking, or auto-advancing content.',
                            remediation_code: '<button type="button" aria-controls="carousel">Pause rotation</button>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class NavigableRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="navigable-skip-links",
            description="A mechanism must be available to bypass blocks of content",
            wcag_criterion="2.4.1",
            level="A",
            impact="moderate",
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        has_skip_link = page.evaluate(
            """() => Array.from(document.links).some(link => {
                const href = link.getAttribute('href') || '';
                const text = (link.textContent || '').toLowerCase();
                const label = (link.getAttribute('aria-label') || '').toLowerCase();
                return href.startsWith('#') && (text.includes('skip') || label.includes('skip'));
            })"""
        )

        if not has_skip_link:
            violations.append(
                build_finding(
                    element="<body>",
                    message="Page is missing a 'Skip to Content' link",
                    suggestion="Add a skip link near the start of the document that targets the main content.",
                    remediation_code='<a class="skip-link" href="#main-content">Skip to content</a>',
                )
            )

        for iframe in page.locator("iframe").all():
            if not iframe.get_attribute("title"):
                violations.append(
                    build_finding(
                        element=locator_html(iframe),
                        message="Iframe missing title attribute",
                        suggestion="Add a descriptive title attribute to the iframe.",
                        remediation_code='<iframe src="report.html" title="Quarterly sales report"></iframe>',
                    )
                )

        return violations


class LinkPurposeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="link-purpose",
            description="Link purpose should be clear from link text or programmatic context",
            wcag_criterion="2.4.4",
            level="A",
            impact="serious",
            applicability="link",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        generic_text = {
            "click here",
            "here",
            "read more",
            "more",
            "learn more",
            "details",
            "view",
            "link",
        }

        links = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href]')).map(link => {
                const label = (
                    link.getAttribute('aria-label') ||
                    link.textContent ||
                    link.getAttribute('title') ||
                    ''
                ).trim().replace(/\\s+/g, ' ');
                const context = (
                    link.closest('article, section, li, p, div')?.textContent ||
                    ''
                ).trim().replace(/\\s+/g, ' ');
                const html = link.outerHTML || '<a>';
                return {
                    href: link.href,
                    label,
                    context,
                    hasProgrammaticContext: link.hasAttribute('aria-labelledby') || link.hasAttribute('aria-describedby'),
                    html: html.length > 140 ? `${html.slice(0, 140)}...` : html
                };
            })"""
        )

        labels_to_hrefs: Dict[str, Set[str]] = {}
        for link in links:
            label = link["label"].lower()
            labels_to_hrefs.setdefault(label, set()).add(link["href"])

        findings = []
        for link in links:
            label = link["label"].lower()
            if not label or label not in generic_text:
                continue
            if link["hasProgrammaticContext"]:
                continue

            repeated = len(labels_to_hrefs.get(label, set())) > 1
            weak_context = len(link["context"]) <= len(link["label"]) + 20
            if repeated or weak_context:
                findings.append(
                    build_finding(
                        element=link["html"],
                        message="Link text is generic and does not clearly communicate purpose",
                        suggestion="Use descriptive link text or connect the link to surrounding context with aria-labelledby.",
                        remediation_code='<a href="/pricing">View pricing plans</a>',
                    )
                )

        return findings


class FocusNotObscuredRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="focus-not-obscured",
            description="Focused interactive elements should not be hidden by sticky UI chrome",
            wcag_criterion="2.4.11",
            level="AA",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const isVisible = el => {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                };
                const focusable = Array.from(document.querySelectorAll(
                    'a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])'
                )).filter(el => !el.hasAttribute('disabled') && isVisible(el));
                const overlays = Array.from(document.querySelectorAll('body *')).filter(el => {
                    if (!isVisible(el)) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    if (!['fixed', 'sticky'].includes(style.position)) return false;
                    return rect.top <= 8 || (window.innerHeight - rect.bottom) <= 8;
                });

                const intersection = (a, b) => {
                    const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
                    const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
                    return x * y;
                };

                if (overlays.length === 0) return [];

                const results = [];

                for (const el of focusable) {
                    const targetRect = el.getBoundingClientRect();
                    const isInViewport = (
                        targetRect.bottom > 0 &&
                        targetRect.top < window.innerHeight &&
                        targetRect.right > 0 &&
                        targetRect.left < window.innerWidth
                    );
                    if (!isInViewport) {
                        continue;
                    }

                    const obscured = overlays.some(overlay => {
                        if (overlay === el || overlay.contains(el) || el.contains(overlay)) return false;
                        return intersection(targetRect, overlay.getBoundingClientRect()) > 0;
                    });

                    if (obscured) {
                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        results.push({
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Focused element appears to be obscured by a sticky header or footer',
                            suggestion: 'Add scroll-margin or adjust sticky UI so focused controls remain fully visible.',
                            remediation_code: ':focus-visible { scroll-margin-top: 6rem; scroll-margin-bottom: 4rem; }',
                        });
                    }

                    if (results.length >= 10) break;
                }

                return results;
            }"""
        )


class PointerGesturesRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="pointer-gestures",
            description="Complex pointer gestures should have a single-pointer alternative",
            wcag_criterion="2.5.1",
            level="A",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const selectors = [
                    '[data-gesture]', '[data-swipe]', '[data-pinch]', '[data-zoom]',
                    '[onswipe]', '[onpinch]', '[style*="touch-action"]'
                ].join(',');
                const altPattern = /next|previous|zoom in|zoom out|open|close|expand|collapse/i;

                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        const style = window.getComputedStyle(el);
                        const gestureValue = [
                            el.getAttribute('data-gesture') || '',
                            el.getAttribute('data-swipe') || '',
                            el.getAttribute('data-pinch') || '',
                            el.getAttribute('data-zoom') || '',
                            style.touchAction || '',
                        ].join(' ').toLowerCase();

                        if (!/(swipe|pinch|zoom|rotate|pan)/.test(gestureValue) && !gestureValue.includes('touch-action')) {
                            return [];
                        }

                        const container = el.closest('section, article, div, main') || el.parentElement || el;
                        const altControl = Array.from(container.querySelectorAll('button, a[href]')).some(control => {
                            const label = (
                                control.textContent ||
                                control.getAttribute('aria-label') ||
                                control.getAttribute('title') ||
                                ''
                            ).trim();
                            return altPattern.test(label);
                        });

                        if (altControl) return [];

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Gesture-driven interaction may require a path-based or multipoint gesture without a simple alternative',
                            suggestion: 'Provide buttons or another single-pointer control for the same action.',
                            finding_type: 'needs_review',
                            remediation_code: '<button type="button">Next slide</button>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class PointerCancellationRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="pointer-cancellation",
            description="Pointer actions should be cancellable before completion",
            wcag_criterion="2.5.2",
            level="A",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => Array.from(document.querySelectorAll('[onmousedown], [onpointerdown], [ontouchstart]'))
                .flatMap(el => {
                    const hasReleaseHandler = (
                        el.hasAttribute('onmouseup') ||
                        el.hasAttribute('onpointerup') ||
                        el.hasAttribute('ontouchend') ||
                        el.hasAttribute('ontouchcancel')
                    );

                    if (hasReleaseHandler) return [];

                    const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                    return [{
                        element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                        message: 'Pointer interaction starts on a down event without an obvious cancel or up-event fallback',
                        suggestion: 'Trigger the committed action on click/pointerup instead of pointerdown, or expose an undo path.',
                        remediation_code: '<button onpointerup="activate()">Save</button>',
                    }];
                })
                .slice(0, 10)"""
        )


class DraggingMovementsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="dragging-movements",
            description="Dragging interactions should expose a non-drag alternative",
            wcag_criterion="2.5.7",
            level="AA",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const selectors = '[draggable="true"], [ondragstart], [ondrop], [data-draggable], [aria-grabbed]';
                const altPattern = /move up|move down|reorder|add|remove|previous|next/i;

                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        const container = el.closest('section, article, li, div') || el.parentElement || el;
                        const hasAlternative = Array.from(container.querySelectorAll('button, a[href]')).some(control => {
                            const label = (
                                control.textContent ||
                                control.getAttribute('aria-label') ||
                                control.getAttribute('title') ||
                                ''
                            ).trim();
                            return altPattern.test(label);
                        });

                        if (hasAlternative) return [];

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Drag-and-drop interaction is present without an obvious non-drag alternative',
                            suggestion: 'Provide move/reorder buttons or another keyboard-compatible control for the same result.',
                            finding_type: 'needs_review',
                            remediation_code: '<button type="button" aria-label="Move item up">Move up</button>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class TargetSizeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="target-size-minimum",
            description="Target size for pointer inputs must be at least 24x24 CSS pixels",
            wcag_criterion="2.5.8",
            level="AA",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("button, a[href], input[type='button'], input[type='submit']").all()
        for loc in locators:
            box = loc.bounding_box()
            if not box:
                continue

            width = box["width"]
            height = box["height"]
            if width < 24 or height < 24:
                violations.append(
                    build_finding(
                        element=locator_html(loc),
                        message=f"Interactive element target size ({width}x{height}) is less than 24x24",
                        suggestion="Increase min-width and min-height, or add padding to expand the clickable area.",
                        remediation_code="button, a { min-width: 24px; min-height: 24px; padding: 4px; }",
                    )
                )
        return violations
