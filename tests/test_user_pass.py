"""Tests for the synthetic user-pass helpers."""

from wcag_auditor.user_pass import UserPassRunner, load_user_pass_config
from wcag_auditor.user_pass.config import UserPassConfig
from wcag_auditor.user_pass.agents import (
    build_executive_system_prompt,
    build_executive_user_prompt,
    EXECUTIVE_AGENT,
)
from wcag_auditor.cli import _render_executive_markdown


def test_load_user_pass_config_reads_dotenv_defaults(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENROUTER_API_KEY=file-key",
                "WCAG_USER_PASS_DEFAULT_MODEL=openrouter/default",
                "WCAG_USER_PASS_COPYWRITER_MODEL=openrouter/copy",
                "WCAG_USER_PASS_MAX_PAGES=4",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("WCAG_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("WCAG_USER_PASS_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("WCAG_USER_PASS_COPYWRITER_MODEL", raising=False)

    config = load_user_pass_config(str(env_file))

    assert config.api_key == "file-key"
    assert config.models["screen_reader"] == "openrouter/default"
    assert config.models["cognitive"] == "openrouter/default"
    assert config.models["copywriter"] == "openrouter/copy"
    assert config.models["executive_writer"] == "openrouter/default"
    assert config.max_pages == 4


class FakeOpenRouterClient:
    def complete_json(self, model, system_prompt, user_prompt):
        if model == "screen-model":
            return {
                "summary": "One likely issue",
                "findings": [
                    {
                        "category": "semantics",
                        "target_text": "Start now",
                        "issue": "CTA lacks context",
                        "evidence": "Primary button label is generic.",
                        "why_it_matters": "People may not understand what happens next.",
                        "suggested_change": "Make the CTA specific to the action.",
                        "confidence": 0.82,
                    }
                ],
            }
        if model == "cognitive-model":
            return {
                "summary": "Same issue from another angle",
                "findings": [
                    {
                        "category": "semantics",
                        "target_text": "Start now",
                        "issue": "CTA is ambiguous",
                        "evidence": "The page excerpt does not explain the button.",
                        "why_it_matters": "Ambiguous actions raise cognitive load.",
                        "suggested_change": "Name the next step directly.",
                        "confidence": 0.76,
                    }
                ],
            }
        if model == "exec-model":
            return {
                "executive_summary": "The site has critical accessibility issues.",
                "risk_assessment": "critical",
                "priority_actions": [
                    {
                        "rule": "complex-alt-text",
                        "priority": "P1",
                        "what": "387 images missing alt text",
                        "why": "Violates WCAG 1.1.1 Level A",
                        "fix": "Add `aria-label` to decorative SVGs.",
                    }
                ],
                "quick_wins": [
                    "Add role='presentation' to all decorative SVG icons."
                ],
            }
        return {
            "summary": "Rewrites",
            "rewrites": [
                {
                    "page_url": "https://example.com",
                    "location": "Primary CTA",
                    "current_text": "Start now",
                    "proposed_text": "Start your accessibility audit",
                    "rationale": "This is more specific and semantically descriptive.",
                    "confidence": 0.71,
                }
            ],
        }


def _make_config():
    return UserPassConfig(
        api_key="key",
        models={
            "screen_reader": "screen-model",
            "cognitive": "cognitive-model",
            "copywriter": "copy-model",
            "executive_writer": "exec-model",
        },
        max_pages=3,
        timeout_seconds=10,
    )


def _make_results():
    return {
        "base_url": "https://example.com",
        "pages_audited": 1,
        "total_passed": 5,
        "pages": [
            {
                "url": "https://example.com",
                "title": "Home",
                "template": "/",
                "page_type": "home",
                "violations_count": 1,
                "manual_reviews_count": 0,
                "warnings_count": 0,
                "passed_count": 5,
            }
        ],
        "sampling": {
            "representative_pages": [
                {"url": "https://example.com", "page_type": "home", "template": "/"}
            ]
        },
        "page_artifacts": [
            {
                "url": "https://example.com",
                "title": "Home",
                "template": "/",
                "page_type": "home",
                "headings": [{"level": "h1", "text": "Accessibility audits"}],
                "landmarks": ["header", "nav", "main", "footer"],
                "link_labels": ["Pricing", "Docs"],
                "button_labels": ["Start now"],
                "form_fields": [],
                "content_excerpt": "Start now and see what breaks.",
                "meta_description": "Home page",
            }
        ],
        "violations": [
            {
                "rule": "complex-alt-text",
                "wcag": "1.1.1",
                "level": "A",
                "impact": "critical",
                "description": "Images must have alt text",
                "suggestion": "Add alt text",
                "element": '<svg id="moon">',
                "message": "Missing alt",
            },
            {
                "rule": "complex-alt-text",
                "wcag": "1.1.1",
                "level": "A",
                "impact": "critical",
                "description": "Images must have alt text",
                "suggestion": "Add alt text",
                "element": '<svg id="sun">',
                "message": "Missing alt",
            },
            {
                "rule": "contrast-minimum",
                "wcag": "1.4.3",
                "level": "AA",
                "impact": "serious",
                "description": "Text must have contrast",
                "suggestion": "Increase contrast",
                "element": "<span>Low</span>",
                "message": "Contrast too low",
            },
        ],
        "manual_reviews": [],
    }


def test_user_pass_runner_aggregates_themes_and_rewrites():
    config = _make_config()
    runner = UserPassRunner(config, client=FakeOpenRouterClient())
    results = _make_results()

    user_pass = runner.run(results)

    assert user_pass["status"] == "completed"
    assert user_pass["pages_reviewed"] == 1
    assert len(user_pass["findings"]) == 2
    assert len(user_pass["themes"]) == 1
    assert user_pass["themes"][0]["agent_ids"] == ["screen_reader", "cognitive"]
    assert user_pass["rewrite_suggestions"][0]["proposed_text"] == "Start your accessibility audit"


# ─── Executive Report Tests ──────────────────────────────────────────

def test_executive_report_pre_processing():
    """Verify the deterministic pre-processing groups violations correctly."""
    config = _make_config()
    runner = UserPassRunner(config, client=FakeOpenRouterClient())
    results = _make_results()

    payload = runner._build_executive_payload(results)

    sc = payload["scorecard"]
    assert sc["total_violations"] == 3
    assert sc["unique_rules_violated"] == 2
    assert sc["level_a_failures"] == 2
    assert sc["level_aa_failures"] == 1
    assert sc["critical_count"] == 2
    assert sc["serious_count"] == 1

    groups = payload["violation_groups"]
    assert len(groups) == 2
    # Groups sorted by impact then count — critical first
    assert groups[0]["rule"] == "complex-alt-text"
    assert groups[0]["count"] == 2
    assert len(groups[0]["sample_elements"]) == 2
    assert groups[1]["rule"] == "contrast-minimum"
    assert groups[1]["count"] == 1

    # Verify synthetic reviewer insights are included
    assert "synthetic_reviewer_insights" in payload
    assert "rewrite_suggestions" in payload


def test_executive_report_generation():
    """Verify the executive report is generated with AI output."""
    config = _make_config()
    runner = UserPassRunner(config, client=FakeOpenRouterClient())
    results = _make_results()

    report = runner.generate_executive_report(results)

    assert report["status"] == "completed"
    assert report["risk_assessment"] == "critical"
    assert "critical accessibility issues" in report["executive_summary"]
    assert len(report["priority_actions"]) == 1
    assert report["priority_actions"][0]["rule"] == "complex-alt-text"
    assert report["priority_actions"][0]["priority"] == "P1"
    assert len(report["quick_wins"]) == 1


def test_executive_report_error_handling():
    """Verify graceful fallback when OpenRouter fails."""
    class FailingClient:
        def complete_json(self, **kwargs):
            raise RuntimeError("API timeout")

    config = _make_config()
    runner = UserPassRunner(config, client=FailingClient())
    results = _make_results()

    report = runner.generate_executive_report(results)

    assert report["status"] == "error"
    assert "API timeout" in report["error"]
    assert report["scorecard"]["total_violations"] == 3
    assert report["priority_actions"] == []


def test_executive_prompt_builders():
    """Verify prompt builders produce valid, non-empty output."""
    system_prompt = build_executive_system_prompt()
    assert "WCAG" in system_prompt
    assert "JSON" in system_prompt

    payload = {"scorecard": {"total_violations": 5}, "violation_groups": []}
    user_prompt = build_executive_user_prompt(payload)
    assert "total_violations" in user_prompt
    assert "prescriptive" in user_prompt.lower()


def test_executive_agent_definition():
    """Verify the EXECUTIVE_AGENT has the expected shape."""
    assert EXECUTIVE_AGENT.agent_id == "executive_writer"
    assert "compliance" in EXECUTIVE_AGENT.role.lower()


def test_render_executive_markdown():
    """Verify the markdown renderer produces the expected structure."""
    data = {
        "scorecard": {
            "pages_audited": 50,
            "total_violations": 1044,
            "unique_rules_violated": 5,
            "critical_count": 387,
            "serious_count": 657,
            "moderate_count": 0,
            "level_a_failures": 387,
            "level_aa_failures": 657,
            "total_passed": 1569,
            "total_manual_reviews": 1,
        },
        "violation_groups": [],
        "executive_summary": "The site needs work.",
        "risk_assessment": "critical",
        "priority_actions": [
            {
                "rule": "complex-alt-text",
                "priority": "P1",
                "what": "387 images missing alt text",
                "why": "Legal risk under ADA",
                "fix": "Add alt attributes.",
            }
        ],
        "quick_wins": ["Add role='presentation' to decorative icons."],
        "synthetic_reviewer_insights": [
            {
                "page_url": "https://example.com",
                "category": "semantics",
                "target_text": "Start now",
                "issue": "CTA lacks context for screen reader users",
                "suggested_change": "Use a more descriptive button label",
                "agent_ids": ["screen_reader", "cognitive"],
                "confidence": 0.82,
            }
        ],
        "rewrite_suggestions": [
            {
                "page_url": "https://example.com",
                "location": "Primary CTA",
                "current_text": "Start now",
                "proposed_text": "Start your accessibility audit",
                "rationale": "More specific and action-oriented",
            }
        ],
    }

    md = _render_executive_markdown(data, "https://example.com", "example.com-20260406.md")

    assert "# WCAG Compliance Executive Report" in md
    assert "**Site:** https://example.com" in md
    assert "**Risk Assessment:** CRITICAL" in md
    assert "## Executive Summary" in md
    assert "The site needs work." in md
    assert "## Compliance Scorecard" in md
    assert "| Total Violations | 1044 |" in md
    assert "## Priority Action Plan" in md
    assert "P1: complex-alt-text" in md
    assert "387 images missing alt text" in md
    assert "Add alt attributes." in md
    assert "## Quick Wins" in md
    assert "role='presentation'" in md
    # Synthetic reviewer insights
    assert "## Synthetic Reviewer Insights" in md
    assert "Start now" in md
    assert "CTA lacks context for screen reader users" in md
    assert "screen_reader, cognitive" in md
    assert "82%" in md
    # Copy changes
    assert "## Recommended Copy Changes" in md
    assert "Start your accessibility audit" in md
    assert "Raw findings: example.com-20260406.md" in md


def test_executive_payload_includes_user_pass_data():
    """Verify reviewer insights and rewrites flow from user_pass to executive payload."""
    config = _make_config()
    runner = UserPassRunner(config, client=FakeOpenRouterClient())

    results = _make_results()
    # Add user_pass data as the CLI would
    results["user_pass"] = {
        "themes": [
            {
                "page_url": "https://example.com",
                "category": "semantics",
                "target_text": "Start now",
                "issue": "CTA lacks context",
                "suggested_change": "Make the CTA specific",
                "agent_ids": ["screen_reader", "cognitive"],
                "confidence": 0.82,
            }
        ],
        "rewrite_suggestions": [
            {
                "page_url": "https://example.com",
                "location": "Primary CTA",
                "current_text": "Start now",
                "proposed_text": "Start your audit",
                "rationale": "More descriptive",
            }
        ],
    }

    payload = runner._build_executive_payload(results)

    assert len(payload["synthetic_reviewer_insights"]) == 1
    assert payload["synthetic_reviewer_insights"][0]["issue"] == "CTA lacks context"
    assert payload["synthetic_reviewer_insights"][0]["agent_ids"] == ["screen_reader", "cognitive"]
    assert len(payload["rewrite_suggestions"]) == 1
    assert payload["rewrite_suggestions"][0]["proposed_text"] == "Start your audit"

