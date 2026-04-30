"""LLM provider abstraction layer for playbook content generation.

Spec reversal from req-55:
  req-55 spec 4 "no LLM call, pure static analysis" -> req-56 OQ-2/OQ-3 introduces LLM for
  business content filling.
  CI compatibility preserved: default Noop provider degrades gracefully when no API key is set.

Auto-detect order (OQ-3 default-pick):
  1. ANTHROPIC_API_KEY env -> AnthropicProvider
  2. OPENAI_API_KEY env -> OpenAIProvider
  3. Ollama localhost (OLLAMA_HOST or http://127.0.0.1:11434) -> OllamaProvider
  4. fallback -> NoopProvider

All providers guarantee:
  - No exception raised on failure (degrade to Noop behavior)
  - Network timeout: 30s, retry once on failure
  - Lazy SDK import (try/except ImportError) to keep CI dependency-free
"""
from __future__ import annotations

import abc
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PlaybookContext:
    """LLM input context (output of static analysis -> used by LLM to generate business desc)."""

    project_name: str
    stack: list  # tech stack (provided by chg-04 SCRIPTS detector)
    layout: str  # top-level directory tree (chg-04 LAYOUT detector)
    domains: list  # inferred domain names (provided by chg-01)
    matched_mode: str  # mode name matched by inferrer (e.g. "Maven multi-module")


@dataclass
class GeneratedContent:
    """LLM output."""

    overview_description: str  # <= 3 sentences project purpose
    tech_decisions: list  # <= 5 technical decision summaries
    domain_descriptions: dict  # domain_name -> one-line responsibility
    domain_keywords: dict  # domain_name -> keyword list (Chinese and English)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class LLMProvider(abc.ABC):
    """LLM provider abstract base class.

    All implementations must guarantee:
    - No exception raised on failure (degrade to Noop behavior)
    - Retry once on network error before degrading
    - Timeout threshold: 30s
    """

    name: str  # for reporting, e.g. "Anthropic / claude-sonnet-4-6"

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check env / config: is this provider currently available?"""

    @abc.abstractmethod
    def generate(self, context: PlaybookContext) -> Optional[GeneratedContent]:
        """Generate content. Returns None on failure (caller should degrade)."""


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

def make_prompt(context: PlaybookContext) -> str:
    """Build prompt from PlaybookContext -> LLM input text."""
    stack_str = ", ".join(context.stack) if context.stack else "unknown"
    domains_str = ", ".join(context.domains) if context.domains else "unknown"
    return (
        "You are a project analyst. Based on the following static analysis results, "
        "generate playbook fill content for this project:\n\n"
        f"Project name: {context.project_name}\n"
        f"Tech stack: {stack_str}\n"
        f"Inferred domains ({context.matched_mode}): {domains_str}\n"
        f"Directory layout:\n{context.layout}\n\n"
        "Please return in JSON format:\n"
        "- overview_description: <= 3 sentences project purpose\n"
        "- tech_decisions: 5 technical decision summaries (list)\n"
        "- domain_descriptions: {each domain} -> one-line responsibility\n"
        "- domain_keywords: {each domain} -> keyword list (Chinese and English synonyms)\n\n"
        "Return JSON only, no markdown code block wrapping."
    )


def parse_response(text: str) -> Optional[GeneratedContent]:
    """Parse LLM JSON output. Returns None on failure (no exception raised)."""
    # Strip markdown code blocks if present
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Remove first line (```json or ```) and last line (```)
        inner_lines = []
        skip_first = True
        for line in lines:
            if skip_first:
                skip_first = False
                continue
            if line.strip() == "```":
                break
            inner_lines.append(line)
        stripped = "\n".join(inner_lines)

    try:
        data = json.loads(stripped)
        return GeneratedContent(
            overview_description=data.get("overview_description", ""),
            tech_decisions=data.get("tech_decisions", []),
            domain_descriptions=data.get("domain_descriptions", {}),
            domain_keywords=data.get("domain_keywords", {}),
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Concrete providers
# ---------------------------------------------------------------------------

def _retry_once(fn, *args, **kwargs):
    """Call fn(*args, **kwargs), retry once on any exception. Returns result or raises."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        return fn(*args, **kwargs)


class AnthropicProvider(LLMProvider):
    """Uses ANTHROPIC_API_KEY env; calls anthropic SDK (if not installed, is_available=False)."""

    name = "Anthropic / claude-sonnet-4-6"
    _MODEL = "claude-sonnet-4-6"
    _TIMEOUT = 30

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, context: PlaybookContext) -> Optional[GeneratedContent]:
        try:
            import anthropic as _anthropic
        except ImportError:
            return None

        prompt = make_prompt(context)

        def _call():
            client = _anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model=self._MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                timeout=self._TIMEOUT,
            )
            # Extract text from content blocks
            if message.content and hasattr(message.content[0], "text"):
                return message.content[0].text
            return str(message.content)

        try:
            result = _retry_once(_call)
            return parse_response(result)
        except Exception:
            return None


class OpenAIProvider(LLMProvider):
    """Uses OPENAI_API_KEY env; calls openai SDK."""

    name = "OpenAI / gpt-4o-mini"
    _MODEL = "gpt-4o-mini"
    _TIMEOUT = 30

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def generate(self, context: PlaybookContext) -> Optional[GeneratedContent]:
        try:
            import openai as _openai
        except ImportError:
            return None

        prompt = make_prompt(context)

        def _call():
            client = _openai.OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
                timeout=self._TIMEOUT,
            )
            response = client.chat.completions.create(
                model=self._MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            return response.choices[0].message.content

        try:
            result = _retry_once(_call)
            return parse_response(result)
        except Exception:
            return None


class OllamaProvider(LLMProvider):
    """Checks OLLAMA_HOST or http://127.0.0.1:11434/api/tags; no API key needed for local."""

    name = "Ollama / llama3.2 (local)"
    _DEFAULT_HOST = "http://127.0.0.1:11434"
    _MODEL = "llama3.2"
    _TIMEOUT = 30

    def __init__(self) -> None:
        self._host = os.environ.get("OLLAMA_HOST", self._DEFAULT_HOST).rstrip("/")

    def _ping(self) -> bool:
        """Check if Ollama is reachable via HTTP HEAD on /api/tags."""
        try:
            req = urllib.request.Request(
                f"{self._host}/api/tags", method="HEAD"
            )
            with urllib.request.urlopen(req, timeout=1) as resp:
                return resp.status < 400
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._ping()

    def generate(self, context: PlaybookContext) -> Optional[GeneratedContent]:
        prompt = make_prompt(context)

        def _call():
            payload = json.dumps(
                {"model": self._MODEL, "prompt": prompt, "stream": False}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{self._host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")

        try:
            result = _retry_once(_call)
            return parse_response(result)
        except Exception:
            return None


class NoopProvider(LLMProvider):
    """Fallback implementation: is_available always True, generate always returns None."""

    name = "Noop (no LLM, fallback)"

    def is_available(self) -> bool:
        return True

    def generate(self, context: PlaybookContext) -> Optional[GeneratedContent]:
        return None


# ---------------------------------------------------------------------------
# Auto-detection (OQ-3 default-pick)
# ---------------------------------------------------------------------------

DEFAULT_PROVIDERS = [AnthropicProvider, OpenAIProvider, OllamaProvider, NoopProvider]


def auto_select_provider(providers=None) -> LLMProvider:
    """Iterate providers in priority order; return first one where is_available() is True.

    Priority (OQ-3):
    1. AnthropicProvider (ANTHROPIC_API_KEY)
    2. OpenAIProvider (OPENAI_API_KEY)
    3. OllamaProvider (OLLAMA_HOST or localhost:11434)
    4. NoopProvider (always available, always returns None)
    """
    if providers is None:
        providers = [P() for P in DEFAULT_PROVIDERS]
    for p in providers:
        if p.is_available():
            return p
    # Guaranteed fallback (NoopProvider is always available, but in case list is empty)
    print("[llm] WARN: no provider available, falling back to Noop", file=sys.stderr)
    return NoopProvider()
