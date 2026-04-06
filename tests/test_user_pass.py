"""Tests for the synthetic user-pass helpers."""

from wcag_auditor.user_pass import UserPassRunner, load_user_pass_config
from wcag_auditor.user_pass.config import UserPassConfig


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


def test_user_pass_runner_aggregates_themes_and_rewrites():
    config = UserPassConfig(
        api_key="key",
        models={
            "screen_reader": "screen-model",
            "cognitive": "cognitive-model",
            "copywriter": "copy-model",
        },
        max_pages=3,
        timeout_seconds=10,
    )
    runner = UserPassRunner(config, client=FakeOpenRouterClient())

    results = {
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
    }

    user_pass = runner.run(results)

    assert user_pass["status"] == "completed"
    assert user_pass["pages_reviewed"] == 1
    assert len(user_pass["findings"]) == 2
    assert len(user_pass["themes"]) == 1
    assert user_pass["themes"][0]["agent_ids"] == ["screen_reader", "cognitive"]
    assert user_pass["rewrite_suggestions"][0]["proposed_text"] == "Start your accessibility audit"
