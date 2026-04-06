# WCAG 2.2 Full Certification Coverage Roadmap

This roadmap outlines the plan to expand the `wcag-auditor` to comprehensive WCAG 2.2 compliance certification at the A and AA levels. The tool currently has **18 active rules** across all four POUR categories with 42 passing tests.

## Phase 1: Engine Foundation & Infrastructure Enhancement ✅

*   ~~**Integrate Headless Browser Engine:**~~ Playwright integrated — all rules evaluate against a live browser context.
*   ~~**Establish DOM Traversal Utilities:**~~ Rules use Playwright locators and `page.evaluate()` for DOM/AOM inspection.
*   ~~**Update Testing Infrastructure:**~~ Tests run against real Playwright `page` fixtures via `pytest-playwright` (42 tests passing).
*   ~~**Create Abstract Rule Interface:**~~ `AbstractRule` base class with `evaluate(page) -> List[Violation]` in `wcag_auditor/rules/__init__.py`.
*   ~~**Rule Metadata Schema:**~~ `RuleMetadata` dataclass with WCAG criterion, level, impact, and applicability fields.

## Phase 2: Perceivable - Level A & AA Coverage 🟡 (Mostly Complete)

Ensure users can perceive all information and user interface components.

*   ~~**Guideline 1.1 Text Alternatives (1.1.1):**~~ `ComplexAltTextRule` — covers `<img>`, `<svg>`, `[role="img"]`, `aria-label`, `aria-labelledby`, and `<title>`. Legacy `MissingAltTextRule` retained as deprecated proxy.
*   ~~**Guideline 1.2 Time-based Media (1.2.2):**~~ `TimeBasedMediaRule` — checks `<video>` and `<audio>` for `<track kind="captions|descriptions|subtitles">`.
    *   🔲 Verify caption tracks reference valid/populated sources (1.2.2 deep check).
    *   🔲 Audio description tracks (1.2.5).
*   ~~**Guideline 1.3 Adaptable:**~~
    *   ~~(1.3.1)~~ `AdaptableLandmarksRule` — validates `<main>` or `[role="main"]` presence.
    *   ~~(1.3.2)~~ `AdaptableReadingSeqRule` — flags positive `tabindex` values that disrupt reading order.
*   **Guideline 1.4 Distinguishable:**
    *   🔲 **Contrast Minimum (1.4.3):** `ContrastMinimumRule` defined but stubbed — pending pixel-level analysis library.
    *   ~~**Focus Appearance (1.4.11):**~~ `FocusAppearanceRule` — detects `outline: none` without fallback focus styles.

## Phase 3: Operable - Level A & AA Coverage 🟡 (Partially Complete)

Ensure user interface components and navigation are operable.

*   **Guideline 2.1 Keyboard Accessible:**
    *   ~~(2.1.1)~~ `KeyboardAccessibilityRule` — flags custom click handlers (`onclick`, `ng-click`, `v-on:click`) on non-native elements lacking both `tabindex` and keyboard event handlers.
    *   🔲 Detect keyboard traps within modals or components (2.1.2).
*   🔲 **Guideline 2.2 Enough Time:** Identify auto-updating content (carousels, timers) and ensure pause controls exist.
*   **Guideline 2.4 Navigable:**
    *   ~~(2.4.1)~~ `NavigableRule` — checks for "Skip to Content" links and `title` attributes on `<iframe>`.
    *   🔲 Clear and descriptive link text context.
    *   🔲 **Focus Visible (2.4.7, AA):** Verify keyboard focus indicators on all interactive elements.
    *   🔲 **Focus Not Obscured (2.4.11, New in 2.2):** Ensure sticky headers/footers don't hide focused elements.
*   **Guideline 2.5 Input Modalities:**
    *   🔲 **Pointer Gestures (2.5.1, A):** Single-pointer alternatives for multipoint gestures.
    *   🔲 **Pointer Cancellation (2.5.2, A):** Down-event abort/undo mechanism.
    *   ~~**Target Size (2.5.8, New in 2.2):**~~ `TargetSizeRule` — checks interactive elements meet 24x24 CSS pixel minimum.
    *   🔲 **Dragging Movements (2.5.7, New in 2.2):** Alternatives for drag-based gestures.

## Phase 4: Understandable - Level A & AA Coverage 🟡 (Partially Complete)

Ensure information and the operation of the user interface are understandable.

*   ~~**Guideline 3.1 Readable:**~~ `MissingLangRule` in core rules validates `lang` attribute on `<html>`.
    *   🔲 Lang changes on inline elements.
*   🔲 **Guideline 3.2 Predictable:** Consistent navigation structures and non-standard context changes.
*   **Guideline 3.3 Input Assistance:**
    *   ~~**Error Identification (3.3.1, A):**~~ `InputAssistanceRule` — verifies `aria-invalid="true"` inputs have `aria-errormessage` or `aria-describedby`.
    *   🔲 **Labels or Instructions (3.3.2, A):** Validate form inputs have associated labels or instructions.
    *   🔲 **Error Suggestion (3.3.3, AA):** Correction suggestions when errors are detected.
    *   🔲 Validate required field indicators.
    *   🔲 **Redundant Entry (3.3.7, New in 2.2):** Flag forms asking for identical information multiple times.
    *   🔲 **Accessible Authentication (3.3.8, New in 2.2):** Login flows without cognitive function test alternatives.
*   ~~**Guideline 1.3.5 Identify Input Purpose:**~~ `IdentifyInputPurposeRule` — flags common input fields (address, phone, email, name) missing `autocomplete` attributes.

## Phase 5: Robust - Level A & AA Coverage 🟡 (Partially Complete)

Ensure content can be interpreted by a wide variety of user agents, including assistive technologies.

*   **Guideline 4.1 Compatible:**
    *   ~~4.1.1 Parsing was deprecated in WCAG 2.2~~ — ID uniqueness is still enforced where it affects ARIA relationships (e.g., `aria-labelledby`, `aria-describedby`).
    *   ~~**Name, Role, Value (4.1.2, A):**~~ `ARIAValidationRule` — validates combobox required attributes (`aria-expanded`, `aria-controls`) and detects invalid ARIA roles.
        *   🔲 Expand to cover all ARIA role required states/properties and value formats.
    *   ~~**Status Messages (4.1.3, AA):**~~ `StatusMessagesRule` — flags `.alert`, `.error`, `.success`, `.toast` elements lacking `role="alert|status|log"` or `aria-live`. (Note: class-name heuristic is framework-dependent; may need expansion.)

## Phase 6: Reporting & Certification Workflow 🟡 (In Progress)

*   🔲 **WCAG EM (Evaluation Methodology) Reporting:** Align JSON and Markdown outputs with the W3C standard format for official reporting.
*   ~~**VPAT / Accessibility Conformance Report (ACR):**~~ `_generate_vpat()` produces VPAT 2.5-compatible Markdown with conformance table, grouped by WCAG criterion. Accessible via `--format vpat`.
*   🔲 **Multi-Page Sampling & SPA Support:** Implement WCAG-EM page sampling strategies for site-level conformance claims, including support for SPA dynamic route discovery and evaluation.
*   🔲 **False Positive Mitigation:** Introduce "Needs Manual Review" categorization for checks that are inherently subjective (e.g., whether `alt` text is actually *descriptive*).
*   🔲 **Actionable Remediation Code:** Extend the engine to generate specific HTML/CSS/JS patch suggestions for common violations.

## Final Phase: Level AAA Coverage (Optional/Stretch) 🚀
*   **Contrast (Enhanced):** 7:1 contrast checks.
*   **Reading Level / Pronunciation checks.**
*   **Target Size (Enhanced).** 
