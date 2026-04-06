# WCAG 2.2 Full Certification Coverage Roadmap

This roadmap is now implemented in the engine. The auditor covers **34 active automated rules** across all four POUR categories and also emits a dedicated **Needs Manual Review** bucket for criteria that require human judgment before a conformance claim is made.

## Phase 1: Engine Foundation & Infrastructure Enhancement ✅

* ~~**Integrate Headless Browser Engine:**~~ Playwright integrated.
* ~~**Establish DOM Traversal Utilities:**~~ Rules inspect live DOM/AOM state in a browser session.
* ~~**Update Testing Infrastructure:**~~ Rule tests use Playwright fixtures and mocked engine/reporter tests cover non-browser paths.
* ~~**Create Abstract Rule Interface:**~~ `AbstractRule` with `metadata` and `evaluate(page)`.
* ~~**Rule Metadata Schema:**~~ `RuleMetadata` carries WCAG criterion, level, impact, and applicability.

## Phase 2: Perceivable - Level A & AA Coverage ✅

* ~~**Guideline 1.1 Text Alternatives (1.1.1):**~~ `ComplexAltTextRule`.
* ~~**Guideline 1.2 Time-based Media:**~~
    * ~~**Captions (1.2.2):**~~ `TimeBasedMediaRule` checks for caption/subtitle tracks and flags empty, broken, or unloaded sources.
    * ~~**Audio Description (1.2.5):**~~ `AudioDescriptionRule` adds a review queue for videos without detectable description tracks or equivalents.
* ~~**Guideline 1.3 Adaptable:**~~
    * ~~(1.3.1)~~ `AdaptableLandmarksRule`.
    * ~~(1.3.2)~~ `AdaptableReadingSeqRule`.
    * ~~(1.3.5)~~ `IdentifyInputPurposeRule`.
* ~~**Guideline 1.4 Distinguishable:**~~
    * ~~**Contrast Minimum (1.4.3):**~~ `ContrastMinimumRule` now performs computed-style contrast checks.
    * ~~**Focus Visible / Appearance:**~~ `FocusAppearanceRule` checks for distinct focus indicators on interactive elements.

## Phase 3: Operable - Level A & AA Coverage ✅

* ~~**Guideline 2.1 Keyboard Accessible:**~~
    * ~~(2.1.1)~~ `KeyboardAccessibilityRule`.
    * ~~(2.1.2)~~ `KeyboardTrapRule` flags dialog-like components that need escape-path review.
* ~~**Guideline 2.2 Enough Time:**~~ `EnoughTimeRule` detects auto-updating regions without pause/stop/resume controls.
* ~~**Guideline 2.4 Navigable:**~~
    * ~~(2.4.1)~~ `NavigableRule`.
    * ~~Clear and descriptive link text context~~ `LinkPurposeRule`.
    * ~~**Focus Not Obscured (2.4.11):**~~ `FocusNotObscuredRule`.
* ~~**Guideline 2.5 Input Modalities:**~~
    * ~~**Pointer Gestures (2.5.1):**~~ `PointerGesturesRule`.
    * ~~**Pointer Cancellation (2.5.2):**~~ `PointerCancellationRule`.
    * ~~**Target Size (2.5.8):**~~ `TargetSizeRule`.
    * ~~**Dragging Movements (2.5.7):**~~ `DraggingMovementsRule`.

## Phase 4: Understandable - Level A & AA Coverage ✅

* ~~**Guideline 3.1 Readable:**~~
    * ~~`MissingLangRule` validates page language.~~
    * ~~Lang changes on inline elements~~ `InlineLanguageChangeRule`.
* ~~**Guideline 3.2 Predictable:**~~ `PredictableNavigationRule` plus site-level representative navigation consistency review.
* ~~**Guideline 3.3 Input Assistance:**~~
    * ~~**Error Identification (3.3.1):**~~ `InputAssistanceRule`.
    * ~~**Labels or Instructions (3.3.2):**~~ `MissingLabelsRule` plus `LabelsInstructionsRule`.
    * ~~**Error Suggestion (3.3.3):**~~ `ErrorSuggestionRule`.
    * ~~Validate required field indicators~~ `RequiredFieldIndicatorsRule`.
    * ~~**Redundant Entry (3.3.7):**~~ `RedundantEntryRule`.
    * ~~**Accessible Authentication (3.3.8):**~~ `AccessibleAuthenticationRule`.

## Phase 5: Robust - Level A & AA Coverage ✅

* ~~**Guideline 4.1 Compatible:**~~
    * ~~4.1.1 Parsing remains out of scope in WCAG 2.2, but ARIA IDREF integrity is validated where it matters.~~
    * ~~**Name, Role, Value (4.1.2):**~~ `ARIAValidationRule` now validates role names, required states/properties, token values, numeric values, and missing IDREF targets.
    * ~~**Status Messages (4.1.3):**~~ `StatusMessagesRule`.

## Phase 6: Reporting & Certification Workflow ✅

* ~~**WCAG EM Reporting:**~~ JSON and Markdown outputs now include representative sampling metadata, methodology, scope, and limitations.
* ~~**VPAT / Accessibility Conformance Report (ACR):**~~ `--format vpat`.
* ~~**Multi-Page Sampling & SPA Support:**~~ Representative sampling, template grouping, SPA route hint discovery, and per-page typing are built into the crawl engine.
* ~~**False Positive Mitigation:**~~ Findings can be routed into `Needs Manual Review` instead of hard failures.
* ~~**Actionable Remediation Code:**~~ Findings can carry HTML/CSS/JS patch suggestions through the reporting pipeline.

## Final Phase: Level AAA Coverage (Optional/Stretch, Not Started) 🚀

* Contrast (Enhanced): 7:1 checks.
* Reading level / pronunciation checks.
* Target Size (Enhanced).
