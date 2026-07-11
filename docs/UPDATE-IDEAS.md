# UPDATE-IDEAS — Next Improvements for wcag-auditor

This is the active backlog as of 2026-07-11. Completed roadmap work and Tranche 1 are recorded in
[CHANGELOG.md](../CHANGELOG.md). The operating principle remains: improve the trustworthiness and
workflow fit of findings before adding broad new coverage.

Effort tags: S = hours, M = days, L = a week or more.

## P0 — Remaining trust and correctness work

### 0.3 Modern keyboard and pointer behavior remains mostly invisible

`KeyboardAccessibilityRule`, `PointerCancellationRule`, and `PredictableNavigationRule` primarily
inspect inline `on*` attributes. Modern sites commonly use delegated or framework event listeners.

Start with a cheap heuristic for non-focusable `role=button`/`role=link` elements and pointer-styled
elements. Treat it as a review signal, not proof of a violation. Consider Chromium-only CDP listener
inspection later, with an explicit limitation for delegated framework listeners. **Effort: S then M**

### 0.5 Complete the Focus Not Obscured interaction check

The current heuristic is correctly routed to `needs_review`, but it still does not focus and scroll a
target before measuring it. For a bounded sample, focus the element, allow browser scroll-into-view,
then measure visible overlap with persistent fixed/sticky overlays. **Effort: M**

### 0.6 Standardize truncation across all rules

Contrast and Focus Not Obscured now expose truncation metadata. Extend the same contract to every
capped rule, render it uniformly, and expose a `--max-findings-per-rule` option. **Effort: M**

### 0.7 Make language-dependent heuristics safe

Several rules use English word lists. Move these lists into per-language data selected by document
language; unknown languages should route the result to `needs_review` rather than pretending an
English heuristic is definitive. Support user extension later through configuration. **Effort: M**

## P1 — Remaining professional workflow work

### 1.2 Screenshots of findings

Add an opt-in `--screenshots` flow, deduped and capped per rule/page. Save locator or bounded-box
evidence as report assets and link it from HTML and Markdown. **Effort: M**

### 1.3 Accessible interactive HTML report

Build a self-contained report with filters, sorting, rule groups, and finding details. It must work
from disk, require no CDN, and meet the same accessibility standard it reports on. **Effort: M–L**

### 1.6 W3C Understanding and technique links

Add static criterion-to-Understanding URLs and optional technique IDs to the report model, then render
them in all human-readable formats. **Effort: S**

### 1.7 Finish authenticated audits

Storage-state login is available. Add only the remaining options that have a clear security model:
repeatable request headers/cookies with secret redaction, then an explicitly opt-in login-script escape
hatch. **Effort: S–M**

### 1.8 Finish crawl controls

Include/exclude patterns, delay, and robots behavior are available. Add sitemap seeding and document
the intended fail-open behavior when robots.txt cannot be read. **Effort: S**

## P2 — Coverage expansion

### 2.1 High-value, deterministic rules

Implement this batch in order:

1. Heading structure: missing/empty `h1`, skipped heading levels, and review-only multiple `h1`.
2. Viewport zoom: `user-scalable=no` and `maximum-scale < 2`.
3. Focusable content inside `aria-hidden=true`.
4. Duplicate IDs referenced by labels or ARIA IDREFs.
5. Table headers and labelled radio/checkbox groups.

Then consider reflow, consistent help, non-text contrast, orientation, and text-spacing survival.
**Effort: S each; M–L for the full batch**

### 2.2 Keyboard-navigation walk

Provide an optional, bounded Tab traversal that records focus stops. Use its evidence for keyboard
accessibility, traps, focus order, focus visibility, and Focus Not Obscured. **Effort: L**

### 2.3 Optional axe-core engine

Offer `--engine native|axe|both`; map axe `incomplete` results to `needs_review`, identify source
engine, and deduplicate using criterion and element identity. **Effort: M**

### 2.4–2.6 Better semantics and configuration

- Reuse browser-computed accessible names in name-dependent rules. **M**
- Add viewport, reduced-motion, dark-mode, and zoom contexts. **M**
- Add `.wcag-auditor.toml` for rule settings, crawl scope, output, and i18n data. **S–M**

## P3 — Differentiators and intelligence

- Run-to-run diffing and trends built on baseline fingerprints. **M**
- Parallel, retryable, cost-accounted, evidence-grounded synthetic-user review. **S–M**
- Opt-in severity-weighted site score with an explicit non-conformance disclaimer. **S**
- WCAG-EM scope notes, conformance target, and richer interchange output. **S–M**

## P4 — Engineering health

1. Consolidate reporter inputs into one intermediate report model before further report expansion. **M**
2. Replace per-element Playwright round trips with single in-page scans where practical. **M**
3. Add bounded parallel page auditing after rule scans are efficient. **M**
4. Make `check` honor `--format` and `--output`; unify report save/slug logic. **S**
5. Add page-level progress rather than a single spinner. **S**
6. Version the JSON output schema. **S**
7. Align Python support and remove unused runtime dependencies. **S**
8. Summarize audio-description review findings to keep the review queue high-signal. **S**

## Recommended sequence

1. Finish trust gaps: 0.3, 0.5–0.7, then reporter consolidation.
2. Deliver screenshots, report links, sitemap support, and the accessible HTML report.
3. Add the small deterministic coverage batch.
4. Build keyboard walk and optional axe-core execution.
5. Add configuration, multi-context, diffs, and intelligence features.
