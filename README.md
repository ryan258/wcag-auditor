# WCAG Auditor

A command-line tool that audits websites for WCAG 2.2 compliance and generates actionable fix reports.

## Features

- Crawls a website and checks pages for WCAG 2.2 violations using a real headless browser (Playwright)
- **34 active rules** spanning all four WCAG 2.2 POUR categories (Perceivable, Operable, Understandable, Robust)
- Emits a dedicated **Needs Manual Review** bucket for criteria that require human judgment before certification
- Generates detailed reports with specific fix recommendations
- Supports multiple output formats (JSON, HTML, Markdown, VPAT 2.5) with WCAG-EM sampling metadata
- Configurable depth and page limits
- Configurable user agent string
- Representative page sampling and SPA route hint discovery for site-level reporting

## Rule Coverage

| Category | Rules | WCAG Criteria |
|---|---|---|
| **Perceivable** | Alt text, captions, audio description review, landmarks, reading sequence, contrast minimum, focus indicators, language-of-parts review | 1.1.1, 1.2.2, 1.2.5, 1.3.1, 1.3.2, 1.4.3, 2.4.7, 3.1.2 |
| **Operable** | Keyboard accessibility, keyboard trap review, enough time controls, skip links, iframe titles, link purpose, focus not obscured, pointer gestures/cancellation, dragging alternatives, target size | 2.1.1, 2.1.2, 2.2.2, 2.4.1, 2.4.4, 2.4.11, 2.5.1, 2.5.2, 2.5.7, 2.5.8 |
| **Understandable** | Predictable navigation, input error identification, labels/instructions, error suggestions, required indicators, redundant entry review, accessible authentication review, input purpose | 3.2.2, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8, 1.3.5 |
| **Robust** | Expanded ARIA validation, IDREF checks, status messages / live regions | 4.1.2, 4.1.3 |
| **Core** | Missing labels, missing lang, empty links, empty buttons, missing title, autofocus | Various Level A |

> **Note:** The auditor now mixes hard failures with **Needs Manual Review** findings. Treat the output as a strong certification workflow, not a substitute for manual accessibility validation on subjective criteria.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

If you already have a project virtual environment, activate it first and then
install the package. On macOS/Homebrew Python, running `pip install -e .`
directly against the system interpreter will fail with an
`externally-managed-environment` error.

## Usage

```bash
# Basic audit of a website
wcag-auditor audit https://example.com

# Audit with specific depth and output format
wcag-auditor audit https://example.com --depth 3 --format html --output report.html

# Generate a VPAT 2.5 Accessibility Conformance Report
wcag-auditor audit https://example.com --format vpat --output vpat-report.md

# Generate a summary report
wcag-auditor summary https://example.com

# Check a single page
wcag-auditor check https://example.com/page
```

If you do not want to activate the virtual environment, you can run the
executable directly:

```bash
.venv/bin/wcag-auditor audit https://example.com
```

## Development

```bash
# Install development dependencies inside an activated virtual environment
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## License

MIT
