# State

- Global constant state: `wcag_auditor.__version__`, `wcag_auditor.__author__`.
- Global host state: `wcag_auditor.auditor` configures root logging at import; `wcag_auditor.cli` instantiates one module-level `Console()`.
- Auditor instance state: `base_url`, `max_depth`, `max_pages`, `timeout`, `user_agent`, `base_domain`, `scheme`, `visited_urls`, `results`, `wcag_rules`.
- Reporter instance state: `results` reference only; treat it as read-only input.
- Per-run mutable locals in `Auditor.audit()`: `urls_to_visit`, `pages_audited`, `all_violations`, `all_warnings`, `all_passed`, `violation_types`, `pages`.
- Orthogonality rule: parser state (`BeautifulSoup`) stays local to the audit layer and dies within the call path; never store it in globals, reporter state, or returned payloads.
- Orthogonality rule: terminal state (`Console`, `Progress`, `Table`) stays in CLI only; core audit logic must remain terminal-agnostic.
- Orthogonality rule: output formatting state stays in `Reporter`; `Auditor` must emit data, not markup.
- Mutation rule: only `Auditor.audit()` may reset `visited_urls` and `results`; external callers must not mutate those fields mid-run.
- Mutation rule: treat `wcag_rules` as immutable after `__init__`; extend via `_load_wcag_rules`, not ad hoc mutation from callers.
- Mutation rule: treat the aggregate result dict as a snapshot after `audit()` returns; downstream code should consume it, not reshape it in place.
- Mutation rule: `Reporter.generate()` must be referentially transparent with respect to `self.results`; no counters, caches, or hidden writebacks.
- Queue rule: crawl order is encoded as a FIFO list of `(url, depth)` tuples; if traversal policy changes, keep ordering explicit and bounded.
- URL state rule: `visited_urls` is the dedupe source of truth; do not add parallel dedupe caches without a single owner.
- Aggregation rule: `violation_types` counts by `rule` only; do not make UI-specific summary tables mutate the audit payload to compensate.
- Safety rule: if new shared state is required, prefer passing it as function input/output over adding module globals.
- Safety rule: if caching is introduced, keep it per-audit or per-instance; never hide cross-run state in module scope.
