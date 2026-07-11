# Changelog

This file records completed work. The active future plan lives in
[roadmap.md](roadmap.md) and [docs/UPDATE-IDEAS.md](docs/UPDATE-IDEAS.md).

## Unreleased — Tranche 1: trustworthy professional workflow

### Added

- Finding provenance and evidence: page URL/title, element selector, accessible name, role, bounding
  box, and frame context where an element can be resolved safely.
- SARIF output, CI impact thresholds, baseline suppression/update, and stderr-only progress output.
- Storage-state authentication, include/exclude crawl scope, robots handling, and crawl delay.
- Manual-review checklist export and merge workflow.
- Complete WCAG 2.2 A/AA VPAT table and generated coverage matrix.

### Changed

- Contrast and Focus Not Obscured uncertainty is routed to manual review; their capped results disclose
  truncation.
- VPAT support claims now require successful automated evidence and do not claim support after a rule
  crash.
- Playwright minimum version is 1.49 to support ARIA snapshots.

### Fixed

- Corrected the WCAG 2.2 A/AA source data to 55 current criteria, including 3.2.6 and 3.3.8 levels and
  removal of obsolete 4.1.1.
- Robots.txt failures no longer silently reduce a crawl to the seed page.
- Ordinary stacking contexts no longer cause contrast checks to become manual review without an actual
  overlapping positioned element.

## Historical foundation

Before Tranche 1, the project delivered the headless Playwright audit engine, the abstract-rule and
metadata model, 34 active rules across the POUR categories, representative crawl/SPA sampling,
WCAG-EM metadata, basic VPAT output, remediation suggestions, and the synthetic user-pass layer.
