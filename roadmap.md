# WCAG Auditor Roadmap

This document contains only forward-looking themes. Completed work is recorded in
[CHANGELOG.md](CHANGELOG.md); the detailed, prioritized backlog is in
[docs/UPDATE-IDEAS.md](docs/UPDATE-IDEAS.md).

## Next: trustworthy coverage

- Detect modern event-bound controls without treating listener presence as proof of keyboard support.
- Perform real focus-and-scroll checks for Focus Not Obscured.
- Finish consistent truncation metadata and a configurable finding cap across every rule.
- Make language-dependent heuristics safe for non-English pages.
- Add high-signal rules for heading structure, viewport zoom, and focusable content hidden from the accessibility tree.

## Next: professional deliverables

- Add screenshots and an accessible, interactive self-contained HTML report.
- Link report findings to W3C Understanding and technique material.
- Complete remaining authenticated-audit options and sitemap seeding.
- Consolidate reporter data into one intermediate report model before expanding formats further.

## Later: differentiated assessment

- Add a bounded keyboard-navigation walk and optional axe-core execution.
- Support multi-context runs, configuration files, run-to-run diffs, and grounded synthetic-user findings.
- Add opt-in management scoring and richer WCAG-EM interchange support.

## Stretch: Level AAA

- Contrast Enhanced (7:1).
- Reading-level and pronunciation checks.
- Target Size Enhanced.
