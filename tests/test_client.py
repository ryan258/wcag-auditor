"""Tests for _extract_completion_json edge cases in client.py."""

import pytest

from wcag_auditor.user_pass.client import _extract_completion_json


class TestExtractCompletionJson:
    """Unit tests for the JSON extraction helper."""

    def _wrap(self, content):
        """Wrap content in a minimal OpenRouter response payload."""
        return {
            "choices": [
                {"message": {"content": content}}
            ]
        }

    def test_bare_json(self):
        """Bare JSON without fences should parse directly."""
        payload = self._wrap('{"summary": "ok", "findings": []}')
        result = _extract_completion_json(payload)
        assert result == {"summary": "ok", "findings": []}

    def test_triple_backtick_json_fence(self):
        """Triple-backtick-wrapped JSON response should be unwrapped."""
        content = '```json\n{"summary": "ok", "findings": []}\n```'
        result = _extract_completion_json(self._wrap(content))
        assert result == {"summary": "ok", "findings": []}

    def test_triple_backtick_no_language_tag(self):
        """Triple-backtick fence without a language tag should still work."""
        content = '```\n{"summary": "bare fence"}\n```'
        result = _extract_completion_json(self._wrap(content))
        assert result == {"summary": "bare fence"}

    def test_tilde_fence(self):
        """Tilde-fence-wrapped JSON response should be unwrapped."""
        content = '~~~json\n{"summary": "tilde fence", "findings": []}\n~~~'
        result = _extract_completion_json(self._wrap(content))
        assert result == {"summary": "tilde fence", "findings": []}

    def test_content_as_list_of_text_blocks(self):
        """Content returned as a list of text block dicts should be joined."""
        payload = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "text", "text": '{"summary":'},
                            {"type": "text", "text": ' "from list"}'},
                        ]
                    }
                }
            ]
        }
        result = _extract_completion_json(payload)
        assert result == {"summary": "from list"}

    def test_non_json_content_raises(self):
        """Non-JSON content should raise RuntimeError."""
        payload = self._wrap("This is not JSON at all")
        with pytest.raises(RuntimeError, match="did not return valid JSON"):
            _extract_completion_json(payload)

    def test_empty_choices_raises(self):
        """Empty choices array should raise RuntimeError."""
        payload = {"choices": []}
        with pytest.raises(RuntimeError, match="did not include choices"):
            _extract_completion_json(payload)

    def test_no_choices_key_raises(self):
        """Missing choices key should raise RuntimeError."""
        payload = {}
        with pytest.raises(RuntimeError, match="did not include choices"):
            _extract_completion_json(payload)

    def test_json_with_surrounding_text(self):
        """JSON embedded in surrounding prose should be extracted."""
        content = 'Here is the result:\n{"summary": "embedded"}\nHope this helps!'
        result = _extract_completion_json(self._wrap(content))
        assert result == {"summary": "embedded"}

    def test_non_object_json_raises(self):
        """JSON array (non-object) should raise RuntimeError."""
        payload = self._wrap('[1, 2, 3]')
        with pytest.raises(RuntimeError, match="non-object JSON"):
            _extract_completion_json(payload)
