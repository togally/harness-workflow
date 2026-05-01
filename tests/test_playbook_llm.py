"""Tests for src/harness_workflow/playbook/llm.py (chg-03: LLM provider abstraction layer).

TC-01  NoopProvider always available + generate returns None
TC-02  auto_select: no env -> falls back to Noop
TC-03  auto_select: ANTHROPIC_API_KEY set -> hits AnthropicProvider
TC-04  auto_select: no Anthropic but OPENAI_API_KEY set -> hits OpenAIProvider
TC-05  auto_select: Ollama reachable (mock urllib 200) -> hits OllamaProvider
TC-06  AnthropicProvider without anthropic SDK -> generate returns None
TC-07  parse_response: valid JSON -> GeneratedContent fields correct
TC-08  parse_response: invalid JSON -> returns None
TC-09  make_prompt: contains key fields (project_name / stack / domains)
TC-10  retry mechanism: generate retries once on transient failure
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
import unittest.mock as mock
from unittest.mock import MagicMock, patch

# Ensure src is importable (worktree dev env)
_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from harness_workflow.playbook.llm import (
    AnthropicProvider,
    DEFAULT_PROVIDERS,
    GeneratedContent,
    NoopProvider,
    OllamaProvider,
    OpenAIProvider,
    PlaybookContext,
    auto_select_provider,
    make_prompt,
    parse_response,
)


def _make_context(**kwargs):
    defaults = dict(
        project_name="test-project",
        stack=["Python", "FastAPI"],
        layout="/src\n  /api\n  /core",
        domains=["api", "core"],
        matched_mode="Python modules",
    )
    defaults.update(kwargs)
    return PlaybookContext(**defaults)


class TestTC01NoopProvider(unittest.TestCase):
    """TC-01: NoopProvider always available; generate always returns None."""

    def test_noop_is_available(self):
        p = NoopProvider()
        self.assertTrue(p.is_available())

    def test_noop_generate_returns_none(self):
        p = NoopProvider()
        ctx = _make_context()
        result = p.generate(ctx)
        self.assertIsNone(result)

    def test_noop_name_contains_noop(self):
        p = NoopProvider()
        self.assertIn("Noop", p.name)


class TestTC02AutoSelectNoEnv(unittest.TestCase):
    """TC-02: auto_select with no env variables falls back to Noop."""

    def test_auto_select_no_env_returns_noop(self):
        env_patch = {
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
            "OLLAMA_HOST": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            # Remove these keys if they exist
            clean_env = {k: v for k, v in os.environ.items()
                         if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
            with patch.dict(os.environ, {}, clear=True):
                os.environ.update(clean_env)
                # Also mock Ollama ping to fail
                with patch("urllib.request.urlopen", side_effect=Exception("no ollama")):
                    provider = auto_select_provider()
        self.assertIn("Noop", provider.name)

    def test_auto_select_explicit_noop_list(self):
        """Passing [NoopProvider()] directly always returns Noop."""
        provider = auto_select_provider([NoopProvider()])
        self.assertIsInstance(provider, NoopProvider)


class TestTC03AutoSelectAnthropic(unittest.TestCase):
    """TC-03: auto_select with ANTHROPIC_API_KEY set -> AnthropicProvider."""

    def test_anthropic_priority(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-dummy"}):
            provider = auto_select_provider()
        self.assertIsInstance(provider, AnthropicProvider)

    def test_anthropic_is_available_with_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-dummy"}):
            p = AnthropicProvider()
            self.assertTrue(p.is_available())

    def test_anthropic_not_available_without_key(self):
        clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update(clean_env)
            p = AnthropicProvider()
            self.assertFalse(p.is_available())


class TestTC04AutoSelectOpenAI(unittest.TestCase):
    """TC-04: auto_select without Anthropic but with OPENAI_API_KEY -> OpenAIProvider."""

    def test_openai_fallback(self):
        clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update(clean_env)
            os.environ["OPENAI_API_KEY"] = "sk-openai-dummy"
            provider = auto_select_provider()
        self.assertIsInstance(provider, OpenAIProvider)

    def test_openai_is_available_with_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-openai-dummy"}):
            p = OpenAIProvider()
            self.assertTrue(p.is_available())


class TestTC05AutoSelectOllama(unittest.TestCase):
    """TC-05: auto_select with Ollama reachable (mock urllib 200) -> OllamaProvider."""

    def test_ollama_detected_when_ping_succeeds(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update(clean_env)
            with patch("urllib.request.urlopen", return_value=mock_resp):
                provider = auto_select_provider()
        self.assertIsInstance(provider, OllamaProvider)

    def test_ollama_is_available_when_ping_succeeds(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            p = OllamaProvider()
            self.assertTrue(p.is_available())

    def test_ollama_not_available_when_ping_fails(self):
        with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
            p = OllamaProvider()
            self.assertFalse(p.is_available())


class TestTC06AnthropicNoSDK(unittest.TestCase):
    """TC-06: AnthropicProvider without anthropic SDK -> generate returns None."""

    def test_generate_returns_none_when_sdk_missing(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-dummy"}):
            # Simulate ImportError when trying to import anthropic
            with patch.dict(sys.modules, {"anthropic": None}):
                p = AnthropicProvider()
                ctx = _make_context()
                result = p.generate(ctx)
        self.assertIsNone(result)


class TestTC07ParseResponseValidJSON(unittest.TestCase):
    """TC-07: parse_response with valid JSON -> GeneratedContent fields correct."""

    def test_parse_valid_json(self):
        payload = {
            "overview_description": "This is a test project.",
            "tech_decisions": ["Use FastAPI", "Use PostgreSQL"],
            "domain_descriptions": {"api": "Handles HTTP requests", "core": "Business logic"},
            "domain_keywords": {"api": ["REST", "HTTP", "endpoint"], "core": ["logic", "service"]},
        }
        text = json.dumps(payload)
        result = parse_response(text)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, GeneratedContent)
        self.assertEqual(result.overview_description, "This is a test project.")
        self.assertEqual(result.tech_decisions, ["Use FastAPI", "Use PostgreSQL"])
        self.assertEqual(result.domain_descriptions["api"], "Handles HTTP requests")
        self.assertIn("REST", result.domain_keywords["api"])

    def test_parse_json_with_markdown_wrapper(self):
        payload = {
            "overview_description": "Wrapped project.",
            "tech_decisions": ["Python"],
            "domain_descriptions": {},
            "domain_keywords": {},
        }
        text = "```json\n" + json.dumps(payload) + "\n```"
        result = parse_response(text)
        self.assertIsNotNone(result)
        self.assertEqual(result.overview_description, "Wrapped project.")


class TestTC08ParseResponseInvalidJSON(unittest.TestCase):
    """TC-08: parse_response with invalid JSON -> returns None."""

    def test_parse_invalid_json_returns_none(self):
        result = parse_response("this is not json at all {{{")
        self.assertIsNone(result)

    def test_parse_empty_string_returns_none(self):
        result = parse_response("")
        self.assertIsNone(result)

    def test_parse_partial_json_returns_none(self):
        result = parse_response('{"overview_description": "incomplete')
        self.assertIsNone(result)


class TestTC09MakePrompt(unittest.TestCase):
    """TC-09: make_prompt contains key fields."""

    def test_prompt_contains_project_name(self):
        ctx = _make_context(project_name="my-awesome-project")
        prompt = make_prompt(ctx)
        self.assertIn("my-awesome-project", prompt)

    def test_prompt_contains_stack(self):
        ctx = _make_context(stack=["Java", "Spring Boot", "Maven"])
        prompt = make_prompt(ctx)
        self.assertIn("Java", prompt)
        self.assertIn("Spring Boot", prompt)

    def test_prompt_contains_domains(self):
        ctx = _make_context(domains=["payment", "inventory", "user"])
        prompt = make_prompt(ctx)
        self.assertIn("payment", prompt)
        self.assertIn("inventory", prompt)

    def test_prompt_contains_matched_mode(self):
        ctx = _make_context(matched_mode="Maven multi-module")
        prompt = make_prompt(ctx)
        self.assertIn("Maven multi-module", prompt)

    def test_prompt_contains_layout(self):
        ctx = _make_context(layout="src/\n  main/\n  test/")
        prompt = make_prompt(ctx)
        self.assertIn("src/", prompt)


class TestTC10RetryMechanism(unittest.TestCase):
    """TC-10: retry mechanism - generate retries once on transient failure."""

    def test_anthropic_retries_on_transient_failure(self):
        """Mock anthropic SDK: both calls raise -> generate returns None (no exception propagated)."""
        call_count = [0]

        def mock_messages_create(**kwargs):
            call_count[0] += 1
            raise ConnectionError("persistent network error")

        mock_anthropic_module = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.side_effect = mock_messages_create
        mock_anthropic_module.Anthropic.return_value = mock_client_instance

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
                p = AnthropicProvider()
                ctx = _make_context()
                result = p.generate(ctx)

        # Both retry attempts failed -> generate must return None (no exception raised)
        self.assertIsNone(result)
        # _retry_once calls once, then retries -> 2 total calls
        self.assertEqual(call_count[0], 2)

    def test_retry_once_succeeds_on_second_attempt(self):
        """Direct test of retry via AnthropicProvider with mocked SDK."""
        expected_json = json.dumps({
            "overview_description": "Success on retry",
            "tech_decisions": [],
            "domain_descriptions": {},
            "domain_keywords": {},
        })

        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("transient")
            msg = MagicMock()
            msg.content = [MagicMock(text=expected_json)]
            return msg

        mock_anthropic_module = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.side_effect = mock_create
        mock_anthropic_module.Anthropic.return_value = mock_client_instance

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
                p = AnthropicProvider()
                ctx = _make_context()
                result = p.generate(ctx)

        self.assertIsNotNone(result)
        self.assertEqual(result.overview_description, "Success on retry")
        self.assertEqual(call_count[0], 2)


class TestDefaultProvidersList(unittest.TestCase):
    """Verify DEFAULT_PROVIDERS contains exactly the expected 4 provider classes."""

    def test_default_providers_count(self):
        self.assertEqual(len(DEFAULT_PROVIDERS), 4)

    def test_default_providers_last_is_noop(self):
        self.assertIs(DEFAULT_PROVIDERS[-1], NoopProvider)

    def test_default_providers_includes_all(self):
        names = {P.__name__ for P in DEFAULT_PROVIDERS}
        self.assertIn("AnthropicProvider", names)
        self.assertIn("OpenAIProvider", names)
        self.assertIn("OllamaProvider", names)
        self.assertIn("NoopProvider", names)


if __name__ == "__main__":
    unittest.main()
