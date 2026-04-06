# Tech Stack

- Runtime shape: Python console application only; no web UI, service, worker, or browser runtime exists here.
- Python floor: `>=3.8` from `pyproject.toml` and `setup.py`; do not introduce syntax or stdlib dependencies that require a higher floor unless packaging changes first.
- Observed local runtime: `.venv/bin/python` is `3.12.11`; keep behavior compatible with the floor, not just the local interpreter.
- Entry point: `wcag-auditor -> wcag_auditor.cli:main`.
- Build backend: `setuptools.build_meta`; package version is sourced from `wcag_auditor.__version__`, and the repository URL is `https://github.com/ryan258/wcag-auditor`.
- Primary runtime deps in `pyproject.toml`: `playwright`, `click`, `rich`, `urllib3`.
- Optional host integration: the synthetic user pass talks to OpenRouter over plain HTTPS using stdlib `urllib`; no OpenAI SDK or `python-dotenv` dependency is required.
- Locked dev deps for Python `>=3.10`: `black 26.3.1`, `flake8 7.3.0`, `mypy 1.19.1`, `pytest 9.0.2`.
- Browser contract: page inspection runs through a live Playwright Chromium session and in-page `page.evaluate(...)` calls; DOM-derived artifacts must stay serializable.
- Network contract: the crawler talks to target sites through Playwright navigation, and the optional synthetic user pass sends OpenRouter HTTPS requests only when `--user-pass` is enabled.
- Config contract: there is no global settings service; the optional user-pass `.env` file is loaded at the CLI seam only when requested.
- File IO contract: only CLI output writes via `Path.write_text(..., encoding="utf-8")`; core audit, user-pass orchestration, and reporting stay memory-only.
- Time contract: timestamps come from `time.strftime` and `datetime.now`; they are runtime side effects and must not be treated as stable test values.
- Logging contract: `logging.basicConfig(...)` runs at module import in `wcag_auditor/auditor.py`; avoid adding more import-time global host setup.
- Host limits: no persistent database, no config file loader, no cache layer, no background queue, no async runtime, no dependency injection container.
- Audit capability limit: automated checks plus the synthetic user pass are advisory layers, not a substitute for manual accessibility validation or disabled human feedback.
- Crawl limits are hard runtime knobs: same-domain only, `http|https` only, queue stops at `max_pages`, recursion stops at `max_depth`.
