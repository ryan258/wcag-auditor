"""Minimal OpenRouter client for JSON-only completions."""

import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import UserPassConfig


class OpenRouterClient:
    """HTTP client for OpenRouter chat completions."""

    def __init__(self, config: UserPassConfig):
        self.config = config

    def complete_json(self, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Request a completion and parse the returned JSON payload."""

        body = json.dumps(
            {
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")

        headers = {
            "Authorization": "Bearer {0}".format(self.config.api_key),
            "Content-Type": "application/json",
        }
        if self.config.referer:
            headers["HTTP-Referer"] = self.config.referer
        if self.config.app_title:
            headers["X-Title"] = self.config.app_title

        request = Request(
            self.config.base_url.rstrip("/") + "/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError("OpenRouter request failed with HTTP {0}: {1}".format(exc.code, detail)) from exc
        except URLError as exc:
            raise RuntimeError("OpenRouter request failed: {0}".format(exc.reason)) from exc

        return _extract_completion_json(payload)


def _extract_completion_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter response did not include choices")

    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        content = "".join(parts)

    if not isinstance(content, str):
        raise RuntimeError("OpenRouter response content was not text")

    content = content.strip()
    # Strip markdown code fences (```json ... ``` or ~~~json ... ~~~)
    for fence in ("```", "~~~"):
        if content.startswith(fence):
            first_newline = content.find("\n")
            if first_newline >= 0:
                content = content[first_newline + 1:]
            else:
                content = content[len(fence):]
            if content.rstrip().endswith(fence):
                content = content.rstrip()
                content = content[:-len(fence)].rstrip()
            break

    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end >= start:
        content = content[start : end + 1]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenRouter model did not return valid JSON: {0}".format(content)) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("OpenRouter model returned non-object JSON")
    return parsed
