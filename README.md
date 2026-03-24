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
pip install -e .
```

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

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## License

MIT