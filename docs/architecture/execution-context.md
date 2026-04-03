# Execution Context

- Entry flow: `wcag_auditor.cli:main -> cli() -> click command -> Auditor.audit() -> Reporter.generate() -> terminal or file output`.
- `audit` command wraps execution in `Progress(...)`; keep progress UX outside domain logic.
- `check` and `summary` commands call `Auditor.audit()` once and render from the returned snapshot; do not add hidden second passes.
- Defensive fetch rule: `_get_page()` must set request headers, apply timeout, call `raise_for_status()`, and trap exceptions.
- Defensive failure rule: `_get_page()` returns `None` on any fetch failure; it does not raise into crawl control flow.
- Defensive translation rule: `_check_page()` converts `None` into an `AuditResult` carrying a `fetch-error` warning.
- Defensive state rule: `Auditor.audit()` resets `visited_urls` and `results` before every run so one instance can be reused safely.
- Defensive loop rule: crawl terminates only on empty queue or `pages_audited >= max_pages`; keep every new loop condition explicit.
- Defensive filter rule: `_extract_links()` ignores empty hrefs, fragments, `javascript:`, `mailto:`, non-HTTP schemes, and off-domain targets.
- Defensive normalization rule: `_extract_links()` strips fragments and keeps query strings; preserve canonicalization in one place.
- Defensive truthfulness rule: append the `low-contrast` skipped warning exactly once per audit, never once per page.
- CLI failure rule: command handlers own user-facing error messages and `sys.exit(1)`; core code should not exit the process.
- Interrupt rule: `audit` handles `KeyboardInterrupt` explicitly; if other commands gain long-running work, give them the same explicit path.
- Output safety rule: HTML report generation must escape all page-derived values before interpolation.
- Determinism rule: avoid letting logging, timestamps, or exception text become part of program control flow.
- Extension rule: new host integrations must follow the same wrapper pattern: narrow side effect, bounded failure, translated warning or raised contract at the CLI seam.
