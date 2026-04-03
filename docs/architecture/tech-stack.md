# Tech Stack

- Runtime shape: Python console application only; no web UI, service, worker, or browser runtime exists here.
- Python floor: `>=3.8` from `pyproject.toml` and `setup.py`; do not introduce syntax or stdlib dependencies that require a higher floor unless packaging changes first.
- Observed local runtime: `.venv/bin/python` is `3.12.11`; keep behavior compatible with the floor, not just the local interpreter.
- Entry point: `wcag-auditor -> wcag_auditor.cli:main`.
- Build backend: `setuptools.build_meta`; package version is sourced from `wcag_auditor.__version__`, and the repository URL is `https://github.com/ryan258/wcag-auditor`.
- Locked runtime deps for Python `>=3.10`: `beautifulsoup4 4.14.3`, `click 8.3.1`, `lxml 6.0.2`, `requests 2.32.5`, `rich 14.3.3`, `urllib3 2.6.3`.
- Locked dev deps for Python `>=3.10`: `black 26.3.1`, `flake8 7.3.0`, `mypy 1.19.1`, `pytest 9.0.2`.
- Parser contract: all HTML parsing is via `BeautifulSoup(..., "lxml")`; do not assume browser DOM behavior.
- Network contract: outbound fetches use `requests.get` with explicit `timeout` and `User-Agent`; no session pooling, retries, auth, or JS execution exists.
- File IO contract: only CLI output writes via `Path.write_text(..., encoding="utf-8")`; core audit and reporting layers stay memory-only.
- Time contract: timestamps come from `time.strftime` and `datetime.now`; they are runtime side effects and must not be treated as stable test values.
- Logging contract: `logging.basicConfig(...)` runs at module import in `wcag_auditor/auditor.py`; avoid adding more import-time global host setup.
- Host limits: no persistent database, no config file loader, no cache layer, no background queue, no async runtime, no dependency injection container.
- Audit capability limit: only 7 WCAG checks are implemented today, and color contrast is intentionally emitted as one skipped warning because the project lacks a rendering engine.
- Crawl limits are hard runtime knobs: same-domain only, `http|https` only, queue stops at `max_pages`, recursion stops at `max_depth`.
