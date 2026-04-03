# Boundaries

- UI boundary: `wcag_auditor/cli.py` owns `click`, `rich`, `Console`, `Table`, `Progress`, `sys.exit`, and output file writes.
- Business boundary: `wcag_auditor/auditor.py` owns crawling, HTML parsing, WCAG rule execution, URL normalization, and aggregate result assembly.
- Presentation boundary: `wcag_auditor/reporter.py` owns format conversion only; it must not fetch pages, mutate crawl state, or print.
- Contract: CLI passes only primitives into `Auditor(base_url, max_depth, max_pages, timeout, user_agent)`.
- Contract: `Auditor.audit()` returns one serializable result dict with keys `base_url`, `pages_audited`, `total_violations`, `total_warnings`, `total_passed`, `violation_types`, `violations`, `warnings`, `passed`, `pages`.
- Contract: `Reporter(results).generate(format)` accepts that aggregate dict and returns a string; no side effects are allowed inside `Reporter`.
- Contract: `AuditResult` is the internal per-page shape with `url`, `violations`, `warnings`, `passed`, `page_title`, `timestamp`.
- Internal-only seam: `_check_page(url)` returns `(AuditResult, BeautifulSoup|None)` for reuse inside `Auditor`; do not expose `BeautifulSoup` outside the audit layer.
- Host API seam: `_get_page(url)` is the only place that talks to `requests`; keep raw HTTP response objects contained there.
- Host API seam: `_extract_links(soup, current_url)` is the only place that normalizes/discovers crawl targets; keep crawl policy there.
- Output seam: HTML escaping belongs in `reporter._esc`; page-derived HTML must never bypass it.
- Exit seam: only CLI commands may convert failures into terminal output and process exit codes.
- Rule seam: each WCAG rule entry must define `description`, `wcag`, `level`, `impact`, and `check`; keep rule metadata adjacent to the callable.
- Data seam: result payloads must stay plain Python data; do not leak console objects, parser objects, response objects, or exceptions into them.
- Test seam: tests patch `wcag_auditor.cli.Auditor` and `wcag_auditor.auditor.requests.get`; preserve those import seams unless tests are updated with the refactor.
- UI stop line: CLI may choose command defaults and rendering widgets, but it must not inspect HTML or infer WCAG logic.
- Domain stop line: `Auditor` may compute violations and warnings, but it must not print, exit, or know about terminal formatting.
