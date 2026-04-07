"""Configuration loading for the synthetic user-pass feature."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


_ENV_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


class UserPassConfigError(ValueError):
    """Raised when the user-pass configuration is incomplete."""


@dataclass(frozen=True)
class UserPassConfig:
    """Resolved configuration for synthetic reviewers and copywriter.

    ``frozen=True`` prevents attribute reassignment but ``models`` is a mutable
    dict.  Callers must not mutate its contents after construction; treat this
    object as fully immutable.
    """

    api_key: str
    models: Dict[str, str]
    max_pages: int = 8
    timeout_seconds: int = 60
    base_url: str = "https://openrouter.ai/api/v1"
    app_title: str = "wcag-auditor"
    referer: Optional[str] = None


def _read_env_file(path: str) -> Dict[str, str]:
    env_path = Path(path)
    if not path or not env_path.exists():
        return {}

    values: Dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()

        match = _ENV_LINE.match(line)
        if not match:
            continue

        key, value = match.groups()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        else:
            # NOTE: Inline comment stripping uses the ` #` delimiter.
            # Unquoted values containing a literal ` #` (e.g. URL fragments
            # or API keys with '#') will be truncated.  Wrap such values in
            # quotes to preserve them.
            comment_index = value.find(" #")
            if comment_index >= 0:
                value = value[:comment_index].rstrip()
        values[key] = value

    return values


def _int_from_env(env: Dict[str, str], key: str, default: int) -> int:
    value = env.get(key)
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise UserPassConfigError("{0} must be an integer".format(key)) from exc
    if parsed <= 0:
        raise UserPassConfigError("{0} must be greater than zero".format(key))
    return parsed


def load_user_pass_config(env_file: str = ".env") -> UserPassConfig:
    """Load OpenRouter-backed user-pass configuration from env vars and .env."""

    file_values = _read_env_file(env_file)
    env = dict(file_values)
    env.update(os.environ)

    api_key = env.get("WCAG_OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY")
    if not api_key:
        raise UserPassConfigError(
            "Set OPENROUTER_API_KEY (or WCAG_OPENROUTER_API_KEY) and the user-pass model variables before using --user-pass."
        )

    default_model = env.get("WCAG_USER_PASS_DEFAULT_MODEL")
    models = {
        "screen_reader": env.get("WCAG_USER_PASS_SCREEN_READER_MODEL") or default_model,
        "cognitive": env.get("WCAG_USER_PASS_COGNITIVE_MODEL") or default_model,
        "copywriter": env.get("WCAG_USER_PASS_COPYWRITER_MODEL") or default_model,
        "executive_writer": env.get("WCAG_USER_PASS_EXECUTIVE_MODEL") or default_model,
    }

    missing = [agent_id for agent_id, model in models.items() if not model]
    if missing:
        raise UserPassConfigError(
            "Missing model configuration for: {0}. Set WCAG_USER_PASS_DEFAULT_MODEL or per-agent model vars.".format(
                ", ".join(sorted(missing))
            )
        )

    return UserPassConfig(
        api_key=api_key,
        models=models,
        max_pages=_int_from_env(env, "WCAG_USER_PASS_MAX_PAGES", 8),
        timeout_seconds=_int_from_env(env, "WCAG_USER_PASS_TIMEOUT_SECONDS", 60),
        base_url=env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        app_title=env.get("OPENROUTER_APP_TITLE", "wcag-auditor"),
        referer=env.get("OPENROUTER_HTTP_REFERER"),
    )
