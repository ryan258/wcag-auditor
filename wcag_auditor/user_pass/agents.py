"""Agent prompts and prompt builders for the synthetic user pass."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class AgentDefinition:
    """Static description for one synthetic reviewer."""

    agent_id: str
    label: str
    role: str
    focus: str


REVIEW_AGENTS = (
    AgentDefinition(
        agent_id="screen_reader",
        label="Screen Reader Reviewer",
        role="semantic and assistive-technology reviewer",
        focus=(
            "Find issues in headings, landmarks, names, instructions, and control semantics that would make "
            "screen-reader navigation or comprehension harder."
        ),
    ),
    AgentDefinition(
        agent_id="cognitive",
        label="Plain-Language Reviewer",
        role="cognitive load and clarity reviewer",
        focus=(
            "Find jargon, ambiguous CTAs, missing context, hard-to-follow instructions, and dense copy that "
            "would likely raise cognitive effort."
        ),
    ),
)

COPYWRITER_AGENT = AgentDefinition(
    agent_id="copywriter",
    label="SEO Copywriter",
    role="semantic, inclusive SEO copywriter",
    focus=(
        "Rewrite headings, link text, CTAs, form instructions, and summary copy to be clearer, more specific, "
        "more inclusive, and more semantically useful without making unsupported claims."
    ),
)


def build_review_system_prompt() -> str:
    """Return the system prompt for one synthetic reviewer."""

    return (
        "You are a synthetic accessibility reviewer, not a disabled human participant. "
        "Only use the evidence provided in the structured page snapshot. "
        "Do not invent visual issues, layout bugs, or user behaviors that are not supported by the input. "
        "Return JSON only with this shape: "
        '{"summary": "short string", "findings": [{"category": "string", "target_text": "string", '
        '"issue": "string", "evidence": "string", "why_it_matters": "string", '
        '"suggested_change": "string", "confidence": 0.0}]}. '
        "Keep at most 5 findings and omit weak claims."
    )


def build_review_user_prompt(
    agent: AgentDefinition,
    page_artifact: Dict[str, Any],
    page_summary: Dict[str, Any],
) -> str:
    """Return the user prompt for one page review."""

    payload = {
        "agent_role": agent.role,
        "focus": agent.focus,
        "page_summary": page_summary,
        "page_artifact": page_artifact,
    }
    return (
        "Review this page snapshot and surface likely usability/accessibility issues in your focus area.\n\n"
        "Structured input:\n"
        "{0}\n".format(json.dumps(payload, indent=2, sort_keys=True))
    )


def build_copywriter_system_prompt() -> str:
    """Return the system prompt for the SEO copywriter."""

    return (
        "You are a semantic and inclusive SEO copywriter. "
        "Use the structured audit data and synthetic reviewer findings to suggest better wording. "
        "Keep recommendations concrete and minimal. "
        "Return JSON only with this shape: "
        '{"summary": "short string", "rewrites": [{"page_url": "string", "location": "string", '
        '"current_text": "string", "proposed_text": "string", "rationale": "string", "confidence": 0.0}]}. '
        "Prefer headings, links, buttons, and form instructions over body paragraphs."
    )


def build_copywriter_user_prompt(
    selected_pages: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
) -> str:
    """Return the user prompt for the copywriter pass."""

    payload = {
        "review_scope": selected_pages,
        "synthetic_findings": findings,
    }
    return (
        "Suggest semantic and inclusive rewrite opportunities for the reviewed pages.\n\n"
        "Structured input:\n"
        "{0}\n".format(json.dumps(payload, indent=2, sort_keys=True))
    )
