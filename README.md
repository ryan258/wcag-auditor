# WCAG Auditor

A command-line tool that audits websites for WCAG 2.2 compliance and generates actionable fix reports.

## Features

- Crawls a website and checks pages for WCAG 2.2 violations
- Generates detailed reports with specific fix recommendations
- Supports multiple output formats (JSON, HTML, Markdown)
- Configurable depth and page limits
- Configurable user agent string

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
