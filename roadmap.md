# WCAG 2.2 Full Certification Coverage Roadmap

This roadmap outlines the plan to expand the `wcag-auditor` from its current limited scope (7 static checks) to a tool capable of comprehensive WCAG 2.2 compliance certification at the A and AA levels.

## Phase 1: Engine Foundation & Infrastructure Enhancement 🏗️

The current static-only architecture prevents the evaluation of dynamic content, complex layouts, and computed contrast ratios. 

*   **Integrate Headless Browser Engine:** Adopt Playwright or Selenium to render the DOM, execute JavaScript, and calculate computed CSS styles.
*   **Establish DOM Traversal Utilities:** Build robust utilities to inspect accessibility trees (AOM), `aria-*` attributes, and stateful components.
*   **Update Testing Infrastructure:** Shift from simple HTML parsing unit tests to E2E-style component tests using real browser contexts.
*   **Create Abstract Rule Interface:** Ensure all rules (static and dynamic) adhere to a unified evaluation interface `evaluate(page) -> List[Violation]`.
*   **Rule Metadata Schema:** Each rule must declare its WCAG success criterion reference, conformance level (A/AA/AAA), impact severity, and applicability — this metadata feeds directly into Phase 6 reporting and VPAT generation.

## Phase 2: Perceivable - Level A & AA Coverage 👁️

Ensure users can perceive all information and user interface components.

*   **Guideline 1.1 Text Alternatives:** Expand `alt` text checks to handle complex images, SVGs, and `aria-label` overrides.
*   **Guideline 1.2 Time-based Media:** Implement checks for `track` elements in `<video>` and `<audio>` tags. Go beyond element presence — verify that caption tracks (1.2.2) and audio description tracks (1.2.5) are actually populated and reference valid sources.
*   **Guideline 1.3 Adaptable:** 
    *   Validate semantic HTML landmarks and structural elements.
    *   Verify reading sequence corresponds to DOM sequence.
*   **Guideline 1.4 Distinguishable:** 
    *   **Contrast (Minimum):** Implement computed visual contrast ratio checking using pixel-level analysis for text and non-text contrast.
    *   **Focus Appearance (New in 2.2):** Ensure focus indicators meet contrast and area requirements.

## Phase 3: Operable - Level A & AA Coverage ⌨️

Ensure user interface components and navigation are operable.

*   **Guideline 2.1 Keyboard Accessible:** 
    *   Verify all interactive elements (`button`, `a`, `input`, etc.) are reachable via Tab sequence.
    *   Detect keyboard traps within modals or components.
*   **Guideline 2.2 Enough Time:** Identify auto-updating content (carousels, timers) and ensure pause controls exist.
*   **Guideline 2.4 Navigable:**
    *   Implement "Skip to Content" link checks.
    *   Verify `title` attributes on `iframe` and page titles.
    *   Check for clear and descriptive link text context.
    *   **Focus Visible (2.4.7, AA):** Verify that keyboard focus indicators are visible on all interactive elements.
    *   **Focus Not Obscured (2.4.11, New in 2.2):** Ensure sticky headers/footers do not hide focused elements.
*   **Guideline 2.5 Input Modalities:**
    *   **Pointer Gestures (2.5.1, A):** Ensure multipoint or path-based gestures have single-pointer alternatives.
    *   **Pointer Cancellation (2.5.2, A):** Verify that down-events don't trigger actions without an abort/undo mechanism.
    *   **Target Size (2.5.8, New in 2.2):** Check that click targets are at least 24x24 CSS pixels.
    *   **Dragging Movements (2.5.7, New in 2.2):** Ensure alternatives exist for actions requiring drag-based gestures.

## Phase 4: Understandable - Level A & AA Coverage 🧠

Ensure information and the operation of the user interface are understandable.

*   **Guideline 3.1 Readable:** Validate `lang` attributes on the `html` element and lang changes on inline elements.
*   **Guideline 3.2 Predictable:** Ensure consistent navigation structures and identify non-standard context changes.
*   **Guideline 3.3 Input Assistance:**
    *   **Error Identification (3.3.1, A):** Verify that input errors are detected and described to the user in text.
    *   **Labels or Instructions (3.3.2, A):** Validate that form inputs have associated labels or instructions.
    *   **Error Suggestion (3.3.3, AA):** Check that known correction suggestions are provided when errors are detected.
    *   Validate required field indicators.
    *   **Redundant Entry (3.3.7, New in 2.2):** Flag forms that ask for identical information multiple times in the same session.
    *   **Accessible Authentication (3.3.8, New in 2.2):** Check that login flows don't rely entirely on cognitive function tests without alternatives.

## Phase 5: Robust - Level A & AA Coverage 🛡️

Ensure content can be interpreted by a wide variety of user agents, including assistive technologies.

*   **Guideline 4.1 Compatible:**
    *   ~~4.1.1 Parsing was deprecated in WCAG 2.2~~ — ID uniqueness is still enforced where it affects ARIA relationships (e.g., `aria-labelledby`, `aria-describedby`).
    *   **Name, Role, Value (4.1.2, A):** Deep check of ARIA role validities, required states/properties, and value formats.
    *   **Status Messages (4.1.3, AA):** Check that dynamic notifications use `aria-live` or appropriate roles.

## Phase 6: Reporting & Certification Workflow 📊

*   **WCAG EM (Evaluation Methodology) Reporting:** Align JSON and Markdown outputs with the W3C standard format for official reporting.
*   **VPAT / Accessibility Conformance Report (ACR):** Generate VPAT 2.5-compatible output — the industry-standard deliverable for procurement and compliance reviews.
*   **Multi-Page Sampling & SPA Support:** Implement WCAG-EM page sampling strategies for site-level conformance claims, including support for SPA dynamic route discovery and evaluation.
*   **False Positive Mitigation:** Introduce "Needs Manual Review" categorization for checks that are inherently subjective (e.g., whether `alt` text is actually *descriptive*).
*   **Actionable Remediation Code:** Extend the engine to generate specific HTML/CSS/JS patch suggestions for common violations.

## Final Phase: Level AAA Coverage (Optional/Stretch) 🚀
*   **Contrast (Enhanced):** 7:1 contrast checks.
*   **Reading Level / Pronunciation checks.**
*   **Target Size (Enhanced).** 
