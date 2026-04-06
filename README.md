# WCAG Auditor

A command-line tool that audits websites for WCAG 2.2 compliance and generates actionable fix reports.

## Features

- Crawls a website and checks pages for WCAG 2.2 violations using a real headless browser (Playwright)
- **18 active rules** spanning all four WCAG 2.2 POUR categories (Perceivable, Operable, Understandable, Robust)
- Generates detailed reports with specific fix recommendations
- Supports multiple output formats (JSON, HTML, Markdown, VPAT 2.5)
- Configurable depth and page limits
- Configurable user agent string

## Rule Coverage

| Category | Rules | WCAG Criteria |
|---|---|---|
| **Perceivable** | Alt text (images, SVGs, ARIA), time-based media captions, landmarks, reading sequence, focus appearance | 1.1.1, 1.2.2, 1.3.1, 1.3.2, 1.4.11 |
| **Operable** | Keyboard accessibility, skip links, iframe titles, target size (24x24 minimum) | 2.1.1, 2.4.1, 2.5.8 |
| **Understandable** | Input error identification, input purpose (autocomplete) | 3.3.1, 1.3.5 |
| **Robust** | ARIA role validation, status messages / live regions | 4.1.2, 4.1.3 |
| **Core** | Missing labels, missing lang, empty links, empty buttons, missing title, autofocus | Various Level A |

> **Note:** Contrast ratio checking (1.4.3) is defined but stubbed out pending a proper pixel-level analysis library. Treat results as a thorough automated audit subset, not full WCAG 2.2 certification coverage — some criteria require manual review.

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
