"""
Configurable LLM client — GitHub Copilot API and OpenAI backends.

Environment variables:
  SLIDE_LLM_PROVIDER  — "copilot" or "openai" (auto-detected if unset)
  GITHUB_TOKEN        — Token for GitHub Copilot API
  OPENAI_API_KEY      — Token for OpenAI API
  SLIDE_LLM_MODEL     — Override model name (default: gpt-5.2)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("slide-builder.llm")

COPILOT_CHAT_URL = "https://api.githubcopilot.com/chat/completions"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-5.2"
DEFAULT_TIMEOUT = 120  # seconds


@dataclass
class Message:
    """A single chat message."""
    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        """Send messages and return the assistant's reply."""
        ...

    @abstractmethod
    def chat_json(self, messages: list[Message], temperature: float = 0.3) -> dict[str, Any]:
        """Send messages and parse the response as JSON."""
        ...

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Convenience: send a system + user message pair."""
        return self.chat(
            [Message("system", system_prompt), Message("user", user_prompt)],
            **kwargs,
        )

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience: send a system + user message pair and parse JSON."""
        return self.chat_json(
            [Message("system", system_prompt), Message("user", user_prompt)],
            **kwargs,
        )


class CopilotClient(LLMClient):
    """GitHub Copilot Chat Completions API client."""

    def __init__(
        self,
        token: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        base_url: str | None = None,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.model = model or os.getenv("SLIDE_LLM_MODEL", DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("SLIDE_COPILOT_URL", COPILOT_CHAT_URL)
        self._timeout = timeout or int(os.getenv("SLIDE_LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required for Copilot client")
        self._client = httpx.Client(
            timeout=self._timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Editor-Version": "vscode/1.96.0",
            "Copilot-Integration-Id": "slide-builder-ghcp",
        }

    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "stream": False,
        }
        resp = self._client.post(self.base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("choices"):
            raise RuntimeError("No choices in Copilot response")
        return data["choices"][0]["message"]["content"]

    def chat_json(self, messages: list[Message], temperature: float = 0.3) -> dict[str, Any]:
        raw = self.chat(messages, temperature=temperature)
        return _parse_json_response(raw)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


class OpenAIClient(LLMClient):
    """OpenAI Chat Completions API client."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("SLIDE_LLM_MODEL", DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("SLIDE_OPENAI_URL", OPENAI_CHAT_URL)
        self._timeout = timeout or int(os.getenv("SLIDE_LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI client")
        self._client = httpx.Client(
            timeout=self._timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }
        resp = self._client.post(self.base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("choices"):
            raise RuntimeError("No choices in OpenAI response")
        return data["choices"][0]["message"]["content"]

    def chat_json(self, messages: list[Message], temperature: float = 0.3) -> dict[str, Any]:
        raw = self.chat(messages, temperature=temperature)
        return _parse_json_response(raw)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse JSON from an LLM response, stripping markdown fences if present."""
    cleaned = raw.strip()
    # Strip markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object or array in the response
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = cleaned.find(start_char)
            end = cleaned.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError:
                    continue
        raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}...")


def get_client(provider: str | None = None) -> LLMClient:
    """
    Create an LLM client based on configuration.

    Resolution order:
    1. Explicit `provider` argument ("copilot" or "openai")
    2. SLIDE_LLM_PROVIDER environment variable
    3. Auto-detect: GITHUB_TOKEN → Copilot, OPENAI_API_KEY → OpenAI
    """
    provider = provider or os.getenv("SLIDE_LLM_PROVIDER", "").lower()

    if provider == "copilot":
        return CopilotClient()
    if provider == "openai":
        return OpenAIClient()

    # Auto-detect
    if os.getenv("GITHUB_TOKEN"):
        logger.info("Auto-detected GitHub token, using Copilot client")
        return CopilotClient()
    if os.getenv("OPENAI_API_KEY"):
        logger.info("Auto-detected OpenAI key, using OpenAI client")
        return OpenAIClient()

    raise RuntimeError(
        "No LLM provider configured. Set GITHUB_TOKEN (for Copilot) "
        "or OPENAI_API_KEY (for OpenAI), or set SLIDE_LLM_PROVIDER explicitly."
    )
