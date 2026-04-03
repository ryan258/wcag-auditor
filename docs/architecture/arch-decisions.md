# Architecture Decisions

- Preserve the 3-part split: `cli.py` is adapter, `auditor.py` is domain engine, `reporter.py` is formatter.
- Preserve the rule-registry pattern in `Auditor._load_wcag_rules()`; add or change rules by editing one registry entry plus one check function.
- Preserve the normalized result schema from `Auditor.audit()`; add new renderers against that schema instead of coupling renderers to crawl internals.
- Preserve `AuditResult` as the per-page boundary object; aggregate once, render later.
- Preserve `wcag_auditor.__version__` as the single version source of truth; downstream metadata should read it, not duplicate it.
- Keep crawling synchronous and single-threaded until ordering, retries, and shared-state contracts are redesigned explicitly.
- Keep the crawler same-domain only; widening scope is an architectural change, not a small feature.
- Keep raw host calls concentrated: HTTP in `_get_page`, filesystem writes in CLI, escaping in `_esc`.
- Keep HTML escaping centralized; any new HTML output path must route page-derived values through `_esc`.
- Keep unsupported checks honest: rule coverage is intentionally partial, and `low-contrast` remains a warning until a browser/rendering seam exists.
- Keep capability gaps surfaced as warnings, never as silent passes.
- Keep command handlers thin; new commands should compose `Auditor` and `Reporter`, not fork crawl logic.
- Keep package metadata synchronized across duplicate sources until version data is consolidated.
- Keep tests patching stable boundaries; move seams only with corresponding test rewrites.
- Keep result payloads serializable and host-neutral so new outputs or APIs can reuse them without re-crawling.
- Keep parser-specific assumptions inside the audit layer; if a browser engine is added later, make it a new adapter, not a cross-cutting change.
- Keep timestamps and logging as peripheral concerns; they must not alter rule outcomes or result counts.
