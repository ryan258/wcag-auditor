"""Shared remediation snippets for common findings."""

from typing import Dict, Optional


DEFAULT_REMEDIATION_SNIPPETS: Dict[str, str] = {
    "missing-labels": '<label for="field-id">Field label</label>\n<input id="field-id" type="text">',
    "missing-lang": '<html lang="en">',
    "empty-links": '<a href="/destination">Descriptive link text</a>',
    "empty-buttons": '<button type="button" aria-label="Close dialog"></button>',
    "missing-title": "<title>Descriptive page title</title>",
    "autofocus-inputs": '<input type="text">',
    "status-messages": '<div role="status" aria-live="polite">Saved successfully</div>',
}


def get_default_remediation_code(rule_id: str) -> Optional[str]:
    """Return a stock remediation snippet for a rule when the rule omitted one."""
    return DEFAULT_REMEDIATION_SNIPPETS.get(rule_id)
