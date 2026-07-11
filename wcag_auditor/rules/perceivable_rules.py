from typing import Any, Dict, List

from playwright.sync_api import Page

from . import AbstractRule, RuleMetadata
from .helpers import build_finding, collect_focus_indicator_findings, locator_html


class ComplexAltTextRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="complex-alt-text",
            description="Images and SVGs must have appropriate alternate text",
            wcag_criterion="1.1.1",
            level="A",
            impact="critical",
            applicability="image",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        locators = page.locator("img, svg, [role='img']").all()
        for loc in locators:
            tag_name = loc.evaluate("el => el.tagName.toLowerCase()")
            role = loc.get_attribute("role")

            if role in {"presentation", "none"}:
                continue

            has_alt = False
            if tag_name == "img":
                has_alt = loc.evaluate("el => el.hasAttribute('alt')")

            if not has_alt:
                has_alt = loc.evaluate(
                    """el => {
                        if (el.hasAttribute('aria-label') && el.getAttribute('aria-label').trim().length > 0) return true;
                        if (el.hasAttribute('aria-labelledby')) return true;
                        if (el.tagName.toLowerCase() === 'svg') {
                            const title = el.querySelector('title');
                            if (title && title.textContent.trim().length > 0) return true;
                        }
                        if (el.hasAttribute('title') && el.getAttribute('title').trim().length > 0) return true;
                        return false;
                    }"""
                )

            if not has_alt:
                violations.append(
                    build_finding(
                        element=locator_html(loc),
                        message="Image/Graphic missing text alternatives",
                        suggestion=(
                            "Add alt text, aria-label, aria-labelledby, or mark purely decorative graphics "
                            "with role='presentation'."
                        ),
                        remediation_code=(
                            '<img src="example.jpg" alt="Describe the meaningful content">\n'
                            '<svg role="img" aria-label="Meaningful icon"></svg>'
                        ),
                    )
                )
        return violations


class TimeBasedMediaRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="time-based-media",
            description="Prerecorded synchronized video must provide captions",
            wcag_criterion="1.2.2",
            level="A",
            impact="serious",
            applicability="media",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        for loc in page.locator("video").all():
            track_state = loc.evaluate(
                """el => {
                    const tracks = Array.from(el.querySelectorAll('track'));
                    const captionTracks = tracks.filter(track =>
                        ['captions', 'subtitles'].includes((track.getAttribute('kind') || '').toLowerCase())
                    );

                    const brokenTrack = captionTracks.find(track => {
                        const src = (track.getAttribute('src') || '').trim();
                        const readyState = typeof track.readyState === 'number' ? track.readyState : 0;
                        const cues = track.track && track.track.cues ? track.track.cues.length : null;
                        return src.length === 0 || readyState === 3 || (readyState === 2 && cues === 0);
                    });

                    return {
                        captionTrackCount: captionTracks.length,
                        brokenTrackHtml: brokenTrack ? trackHtml(brokenTrack) : null
                    };

                    function trackHtml(track) {
                        const html = track.outerHTML || '<track>';
                        return html.length > 140 ? `${html.slice(0, 140)}...` : html;
                    }
                }"""
            )

            if track_state["captionTrackCount"] == 0:
                findings.append(
                    build_finding(
                        element=locator_html(loc),
                        message="Video is missing a captions or subtitles track",
                        suggestion="Add a populated <track kind='captions'> or <track kind='subtitles'> file.",
                        remediation_code=(
                            "<video controls>\n"
                            "  <source src=\"movie.mp4\" type=\"video/mp4\">\n"
                            "  <track kind=\"captions\" srclang=\"en\" src=\"captions-en.vtt\" default>\n"
                            "</video>"
                        ),
                    )
                )
                continue

            if track_state["brokenTrackHtml"]:
                findings.append(
                    build_finding(
                        element=track_state["brokenTrackHtml"],
                        message="Caption track source is empty, failed to load, or contains no cues",
                        suggestion="Point the caption track at a valid VTT file with synchronized cues.",
                        remediation_code='<track kind="captions" srclang="en" src="captions-en.vtt" default>',
                    )
                )
                continue

        return findings


class AudioDescriptionRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="audio-description-track",
            description="Prerecorded video should expose audio description or an equivalent alternative",
            wcag_criterion="1.2.5",
            level="AA",
            impact="serious",
            applicability="media",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        for loc in page.locator("video").all():
            has_description_track = loc.evaluate(
                """el => Array.from(el.querySelectorAll('track')).some(track =>
                    (track.getAttribute('kind') || '').toLowerCase() === 'descriptions'
                )"""
            )
            if not has_description_track:
                findings.append(
                    build_finding(
                        element=locator_html(loc),
                        message="Video has no detectable audio description track",
                        suggestion=(
                            "Provide audio descriptions, an alternate described version, or document that the "
                            "video has no information conveyed visually alone."
                        ),
                        finding_type="needs_review",
                    )
                )
        return findings


class AdaptableLandmarksRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="adaptable-landmarks",
            description="Pages should use semantic landmarks for structure",
            wcag_criterion="1.3.1",
            level="A",
            impact="moderate",
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        has_main = page.evaluate(
            "() => document.querySelector('main') !== null || document.querySelector('[role=\"main\"]') !== null"
        )
        if has_main:
            return []
        return [
            build_finding(
                element="<body>",
                message="Page is missing a main landmark",
                suggestion="Wrap the primary content in a <main> element or an element with role='main'.",
                remediation_code="<main id=\"main-content\">\n  <!-- primary page content -->\n</main>",
            )
        ]


class AdaptableReadingSeqRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="reading-sequence",
            description="Elements with positive tabindex can disrupt logical reading sequence",
            wcag_criterion="1.3.2",
            level="A",
            impact="serious",
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        violations = []
        for loc in page.locator("[tabindex]").all():
            tabindex_val = loc.get_attribute("tabindex")
            try:
                if tabindex_val and int(tabindex_val) > 0:
                    violations.append(
                        build_finding(
                            element=locator_html(loc),
                            message="Element uses a positive tabindex which disrupts predictable navigation",
                            suggestion="Use tabindex='0' or '-1' and rely on DOM order for navigation.",
                            remediation_code='<button tabindex="0">Focusable in DOM order</button>',
                        )
                    )
            except ValueError:
                continue
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
            applicability="text",
            coverage_type="partial-heuristic"
        )

    def evaluate(self, page: Page, cap: int = 20) -> List[Dict[str, Any]]:
        findings = page.evaluate(
            """() => {
                const selector = [
                    'p', 'span', 'a[href]', 'button', 'label', 'li', 'td', 'th',
                    'input', 'textarea', 'select', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
                ].join(',');

                const parseColor = value => {
                    if (!value || value === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
                    const rgb = value.match(/rgba?\\(([^)]+)\\)/i);
                    if (rgb) {
                        const parts = rgb[1].split(',').map(part => Number.parseFloat(part.trim()));
                        return {
                            r: parts[0],
                            g: parts[1],
                            b: parts[2],
                            a: Number.isFinite(parts[3]) ? parts[3] : 1,
                        };
                    }

                    const hex = value.trim().replace('#', '');
                    if (hex.length === 3) {
                        return {
                            r: Number.parseInt(`${hex[0]}${hex[0]}`, 16),
                            g: Number.parseInt(`${hex[1]}${hex[1]}`, 16),
                            b: Number.parseInt(`${hex[2]}${hex[2]}`, 16),
                            a: 1,
                        };
                    }
                    if (hex.length === 6) {
                        return {
                            r: Number.parseInt(hex.slice(0, 2), 16),
                            g: Number.parseInt(hex.slice(2, 4), 16),
                            b: Number.parseInt(hex.slice(4, 6), 16),
                            a: 1,
                        };
                    }
                    return null;
                };

                const blend = (fg, bg) => {
                    if (!fg || !bg) return null;
                    const alpha = Number.isFinite(fg.a) ? fg.a : 1;
                    if (alpha >= 1) return { r: fg.r, g: fg.g, b: fg.b };
                    return {
                        r: Math.round((fg.r * alpha) + (bg.r * (1 - alpha))),
                        g: Math.round((fg.g * alpha) + (bg.g * (1 - alpha))),
                        b: Math.round((fg.b * alpha) + (bg.b * (1 - alpha))),
                    };
                };

                const luminance = color => {
                    const channels = [color.r, color.g, color.b].map(value => {
                        const normalized = value / 255;
                        return normalized <= 0.03928
                            ? normalized / 12.92
                            : ((normalized + 0.055) / 1.055) ** 2.4;
                    });
                    return (0.2126 * channels[0]) + (0.7152 * channels[1]) + (0.0722 * channels[2]);
                };

                const contrastRatio = (a, b) => {
                    const l1 = luminance(a);
                    const l2 = luminance(b);
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                };

                const backgroundFor = el => {
                    let current = el;
                    while (current) {
                        const parsed = parseColor(window.getComputedStyle(current).backgroundColor);
                        if (parsed && parsed.a > 0) {
                            return parsed;
                        }
                        current = current.parentElement;
                    }
                    return { r: 255, g: 255, b: 255, a: 1 };
                };

                const textFor = el => {
                    if (['input', 'textarea', 'select'].includes(el.tagName.toLowerCase())) {
                        return (el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim();
                    }
                    return (el.innerText || el.textContent || '').trim();
                };

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

                const hasPositionedOverlap = el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return false;

                    const points = [
                        [rect.left + (rect.width / 2), rect.top + (rect.height / 2)],
                        [rect.left + 1, rect.top + 1],
                        [rect.right - 1, rect.bottom - 1],
                    ];

                    return points.some(([x, y]) => {
                        if (x < 0 || y < 0 || x >= window.innerWidth || y >= window.innerHeight) return false;
                        const stack = document.elementsFromPoint(x, y);
                        const targetIndex = stack.findIndex(candidate => candidate === el || el.contains(candidate));
                        if (targetIndex <= 0) return false;

                        return stack.slice(0, targetIndex).some(candidate => {
                            if (candidate === el || candidate.contains(el) || el.contains(candidate)) return false;
                            const style = window.getComputedStyle(candidate);
                            const background = parseColor(style.backgroundColor);
                            const isPositioned = ['absolute', 'fixed', 'sticky'].includes(style.position)
                                || style.zIndex !== 'auto';
                            return isPositioned
                                && style.visibility !== 'hidden'
                                && Number.parseFloat(style.opacity || '1') > 0
                                && (
                                    style.backgroundImage !== 'none'
                                    || (background && background.a > 0)
                                );
                        });
                    });
                };

                const getUncertainty = el => {
                    if (hasPositionedOverlap(el)) {
                        return 'Text has overlapping positioned content — verify contrast manually';
                    }
                    let current = el;
                    while (current) {
                        const style = window.getComputedStyle(current);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none' && bgImage !== '') {
                            return 'Text over image or gradient — verify contrast manually';
                        }
                        const parsedBg = parseColor(style.backgroundColor);
                        if (parsedBg && parsedBg.a > 0) {
                            if (parsedBg.a < 1) {
                                return 'Background color is semi-transparent — verify contrast manually';
                            }
                            break;
                        }
                        current = current.parentElement;
                    }

                    current = el;
                    while (current) {
                        const style = window.getComputedStyle(current);
                        const opacity = Number.parseFloat(style.opacity || '1');
                        if (opacity < 1) {
                            return 'Element or ancestor has opacity < 1 — verify contrast manually';
                        }
                        const parsedBg = parseColor(style.backgroundColor);
                        if (parsedBg && parsedBg.a > 0) {
                            break;
                        }
                        current = current.parentElement;
                    }
                    return null;
                };

                const elements = Array.from(document.querySelectorAll(selector));
                const allFindings = [];

                for (const el of elements) {
                    const text = textFor(el);
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    if (!text || text.length < 2) continue;
                    if (rect.width === 0 || rect.height === 0) continue;
                    if (style.display === 'none' || style.visibility === 'hidden') continue;
                    if (Number.parseFloat(style.opacity || '1') === 0) continue;

                    const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                    const truncatedHtml = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                    const stableSel = getStableSelector(el);

                    // 1. Check for uncertainty
                    const uncertaintyMsg = getUncertainty(el);
                    if (uncertaintyMsg) {
                        allFindings.push({
                            element: truncatedHtml,
                            selector: stableSel,
                            message: uncertaintyMsg,
                            suggestion: 'Verify contrast ratio manually using an eyedropper or diagnostic tool.',
                            finding_type: 'needs_review',
                            remediation_code: `${el.tagName.toLowerCase()} {\\n  color: #1a1a1a;\\n  background-color: #ffffff;\\n}`
                        });
                        continue;
                    }

                    // 2. Standard contrast check
                    const foreground = parseColor(style.color);
                    const background = backgroundFor(el);
                    if (!foreground || !background) continue;

                    const resolvedForeground = blend(foreground, background);
                    const ratio = contrastRatio(resolvedForeground, background);
                    const fontSize = Number.parseFloat(style.fontSize || '16');
                    const fontWeight = Number.parseInt(style.fontWeight || '400', 10) || 400;
                    const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
                    const minimum = isLargeText ? 3 : 4.5;

                    if (ratio + 0.01 < minimum) {
                        allFindings.push({
                            element: truncatedHtml,
                            selector: stableSel,
                            message: `Text contrast ratio ${ratio.toFixed(2)}:1 is below the required ${minimum}:1`,
                            suggestion: 'Increase the difference between foreground and background colors for readable text.',
                            remediation_code: `${el.tagName.toLowerCase()} {\\n  color: #1a1a1a;\\n  background-color: #ffffff;\\n}`
                        });
                    }
                }

                return allFindings;
            }"""
        )
        total_matched = len(findings)
        sliced = findings[:cap]
        for f in sliced:
            f["truncated"] = total_matched > cap
            f["total"] = total_matched
        return sliced


class FocusAppearanceRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="focus-appearance",
            description="Focus indicators must be visible and distinct when interactive elements receive focus",
            wcag_criterion="2.4.7",
            level="AA",
            impact="serious",
            applicability="interactive",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return collect_focus_indicator_findings(
            page,
            message="Interactive element appears to have no distinct focus indicator",
            suggestion=(
                "Do not remove the browser focus ring unless you provide a visible replacement such as an "
                "outline, box-shadow, or border change."
            ),
        )


class InlineLanguageChangeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="inline-language-change",
            description="Language changes within a page should be marked with valid lang attributes",
            wcag_criterion="3.1.2",
            level="AA",
            impact="moderate",
            applicability="content",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const documentLang = (document.documentElement.getAttribute('lang') || '').trim().toLowerCase();
                const candidates = Array.from(document.querySelectorAll('span, em, strong, i, b, q, cite, abbr'));
                const suspiciousLanguage = /[\\u00C0-\\u024F\\u0370-\\u03FF\\u0400-\\u04FF]/;
                const langPattern = /^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$/;

                return candidates.flatMap(el => {
                    const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                    const snippet = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                    const text = (el.textContent || '').trim();
                    const lang = (el.getAttribute('lang') || '').trim();

                    if (lang && !langPattern.test(lang)) {
                        return [{
                            element: snippet,
                            message: `Inline lang attribute '${lang}' is not a valid BCP 47 language tag`,
                            suggestion: "Use a valid language code such as 'fr' or 'es-MX'.",
                            remediation_code: '<span lang="fr">Bonjour</span>',
                        }];
                    }

                    if (!lang && documentLang && text.length >= 2 && suspiciousLanguage.test(text)) {
                        return [{
                            element: snippet,
                            message: "Inline text appears to switch language without a lang attribute",
                            suggestion: "Wrap foreign-language words or phrases in an element with an appropriate lang attribute.",
                            finding_type: 'needs_review',
                        }];
                    }

                    return [];
                }).slice(0, 10);
            }"""
        )
