# Execution Context

- Entry flow: `wcag_auditor.cli:main -> cli() -> click command -> Auditor.audit() -> Reporter.generate() -> terminal or file output`.
- `audit` command wraps execution in `Progress(...)`; keep progress UX outside domain logic.
- `audit` may optionally invoke `UserPassRunner` after the crawl snapshot is complete; that analysis must be explicit behind `--user-pass`, not a hidden second crawl.
- `check` and `summary` commands call `Auditor.audit()` once and render from the returned snapshot; do not add hidden second passes there.
- Defensive navigation rule: `page.goto()` failures are translated into `fetch-error` warnings and must not increment `pages_audited`.
- Defensive state rule: `Auditor.audit()` resets `visited_urls` and `results` before every run so one instance can be reused safely.
- Defensive loop rule: crawl terminates only on empty queue or `pages_audited >= max_pages`; keep every new loop condition explicit.
- Defensive filter rule: `_extract_links()` ignores empty hrefs, fragments, `javascript:`, `mailto:`, non-HTTP schemes, and off-domain targets.
- Defensive normalization rule: `_extract_links()` strips fragments and keeps query strings; preserve canonicalization in one place.
- Defensive truthfulness rule: AI reviewer output must remain in the `user_pass` bucket and must never change WCAG counts or conformance wording.
- CLI failure rule: command handlers own user-facing error messages and `sys.exit(1)`; core code should not exit the process.
- Interrupt rule: `audit` handles `KeyboardInterrupt` explicitly; if other commands gain long-running work, give them the same explicit path.
- Output safety rule: HTML report generation must escape all page-derived values before interpolation.
- Determinism rule: avoid letting logging, timestamps, or exception text become part of program control flow.
- Extension rule: new host integrations must follow the same wrapper pattern: narrow side effect, bounded failure, translated report payload, and CLI-owned activation.
