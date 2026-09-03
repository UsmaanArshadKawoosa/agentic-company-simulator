from __future__ import annotations

import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.agents.decisions import AgentDecision

logger = logging.getLogger("agent_company_simulator")


class LLMError(Exception):
    """Base exception for LLM-related errors."""


class LLMTimeoutError(LLMError):
    """LLM call exceeded timeout."""


class LLMRateLimitError(LLMError):
    """LLM provider rate limited the request."""


class LLMProviderError(LLMError):
    """LLM provider returned an error."""


class LLMParseError(LLMError):
    """LLM output could not be parsed."""


class LLMService(ABC):
    """Abstraction over an LLM provider.

    The rest of the application depends on this interface rather than on a
    concrete provider SDK.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        ...

    @abstractmethod
    def structured_generate(
        self,
        prompt: str,
        schema: type | dict | None = None,
        **kwargs: Any,
    ) -> dict:
        ...


class NoOpLLMService(LLMService):
    """Deterministic placeholder implementation (no provider calls).

    Returns structured stub results so the rest of the system can be wired up
    and later swapped for a real provider implementation.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return f"[NoOpLLM] received prompt of length {len(prompt)}."

    def structured_generate(
        self,
        prompt: str,
        schema: type | dict | None = None,
        **kwargs: Any,
    ) -> dict:
        return {
            "placeholder": True,
            "prompt_length": len(prompt),
            "note": "Replace NoOpLLMService with a real provider to enable LLM behavior.",
        }


class MockLLMService(LLMService):
    """Returns predefined structured decisions for tests.

    Accepts an optional mapping of role -> decision so tests can control agent
    behavior without real API credentials. Also supports a callable script that
    receives (role, day, context) for context-aware test behavior.
    """

    def __init__(
        self,
        decisions: dict[str, dict] | None = None,
        script: "callable | None" = None,
        fail_roles: set[str] | None = None,
        malformed_roles: set[str] | None = None,
    ) -> None:
        self._decisions: dict[str, dict] = decisions or {}
        self._script = script
        self._fail_roles: set[str] = fail_roles or set()
        self._malformed_roles: set[str] = malformed_roles or set()

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return "[MockLLM] generated text."

    def structured_generate(
        self,
        prompt: str,
        schema: type | dict | None = None,
        **kwargs: Any,
    ) -> dict:
        role = kwargs.get("role", "AGENT")
        day = kwargs.get("day", 1)
        context = kwargs.get("context")

        # Simulate failure injection.
        if role in self._fail_roles:
            raise LLMProviderError(f"Mock failure injected for role {role}")

        # Simulate malformed output.
        if role in self._malformed_roles:
            return {"invalid_key": "this is not a valid decision"}

        # Script takes precedence for dynamic behavior.
        if self._script is not None:
            try:
                result = self._script(role, day, context)
                if result is not None:
                    return dict(result)
            except Exception:
                pass
        if role in self._decisions:
            return dict(self._decisions[role])
        return {
            "action": "NO_ACTION",
            "reasoning": "Mock default: no action configured for this role.",
            "confidence": 0.5,
        }


class RealLLMService(LLMService):
    """Provider-backed LLM service.

    Supports Anthropic, OpenAI, Gemini, and Ollama. Configuration comes from
    environment variables only; credentials are never hardcoded.

    Environment variables:
        LLM_PROVIDER   - "anthropic" | "openai" | "gemini" | "ollama"
        LLM_MODEL      - model id
        LLM_API_KEY    - provider API key (required for anthropic/openai/gemini,
                         not required for ollama)
        LLM_MAX_TOKENS - max tokens for the response (optional)
        LLM_TEMPERATURE - sampling temperature (optional, default 0.0)
        LLM_TIMEOUT    - timeout in seconds (optional, default 30)
        OLLAMA_BASE_URL - base URL for the local Ollama server (optional,
                          default http://localhost:11434)
    """

    # Providers that authenticate with an API key.
    _KEYED_PROVIDERS = frozenset({"anthropic", "openai", "gemini"})
    # All supported real providers.
    _SUPPORTED_PROVIDERS = frozenset({"anthropic", "openai", "gemini", "ollama"})

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: int = 30,
        max_retries: int = 2,
    ) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "")).lower()
        self.model = model or os.getenv("LLM_MODEL", "")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_tokens = max_tokens
        self.temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.provider:
            raise ValueError("LLM_PROVIDER is required for RealLLMService.")
        if self.provider in self._KEYED_PROVIDERS and not self.api_key:
            raise ValueError("LLM_API_KEY is required for RealLLMService.")
        if self.provider not in self._SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self._call_with_retry(prompt, **kwargs)

    def structured_generate(
        self,
        prompt: str,
        schema: type | dict | None = None,
        **kwargs: Any,
    ) -> dict:
        """Produce a structured dict. Parses JSON from the model output and validates."""
        raw = self._call_with_retry(prompt, **kwargs)
        return self._parse_json(raw)

    def _call_with_retry(self, prompt: str, **kwargs: Any) -> str:
        """Call LLM with bounded retries for transient failures."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.provider == "anthropic":
                    return self._anthropic_generate(prompt, **kwargs)
                if self.provider == "openai":
                    return self._openai_generate(prompt, **kwargs)
                if self.provider == "gemini":
                    return self._gemini_generate(prompt, **kwargs)
                return self._ollama_generate(prompt, **kwargs)
            except LLMTimeoutError:
                raise  # Don't retry timeouts.
            except LLMRateLimitError:
                raise  # Don't retry rate limits.
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    logger.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, self.max_retries + 1, exc)
                    continue
        raise LLMProviderError(f"LLM call failed after {self.max_retries + 1} attempts: {last_error}")

    # --- Anthropic ---

    def _anthropic_generate(self, prompt: str, **kwargs: Any) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        model = self.model or kwargs.get("model", "claude-sonnet-4-6")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]

        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                messages=messages,
            )
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(f"Anthropic timeout: {exc}") from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code == 429:
                raise LLMRateLimitError(f"Anthropic rate limit: {exc}") from exc
            raise LLMProviderError(f"Anthropic API error: {exc}") from exc

        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

    # --- OpenAI ---

    def _openai_generate(self, prompt: str, **kwargs: Any) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, timeout=self.timeout)
        model = self.model or kwargs.get("model", "gpt-4o-mini")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]

        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                messages=messages,
            )
        except Exception as exc:
            if "timeout" in str(exc).lower():
                raise LLMTimeoutError(f"OpenAI timeout: {exc}") from exc
            if "rate limit" in str(exc).lower():
                raise LLMRateLimitError(f"OpenAI rate limit: {exc}") from exc
            raise LLMProviderError(f"OpenAI API error: {exc}") from exc

        return response.choices[0].message.content or ""

    # --- Gemini ---

    def _gemini_generate(self, prompt: str, **kwargs: Any) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        model = self.model or kwargs.get("model") or "gemini-2.5-flash"
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=self.temperature,
                ),
            )
        except Exception as exc:
            # Never surface the API key in error messages.
            msg = self._scrub_key(str(exc))
            low = msg.lower()
            if "timeout" in low or "timed out" in low:
                raise LLMTimeoutError(f"Gemini timeout: {msg}") from exc
            if "rate limit" in low or "429" in low:
                raise LLMRateLimitError(f"Gemini rate limit: {msg}") from exc
            raise LLMProviderError(f"Gemini API error: {msg}") from exc

        # google-genai returns the generated text on response.text.
        return getattr(response, "text", "") or ""

    def _scrub_key(self, message: str) -> str:
        """Redact the API key from a message so it is never leaked."""
        if self.api_key:
            message = message.replace(self.api_key, "<redacted>")
        return message

    # --- Ollama ---

    def _ollama_generate(self, prompt: str, **kwargs: Any) -> str:
        import httpx

        model = self.model or kwargs.get("model")
        if not model:
            raise LLMProviderError("LLM_MODEL is required for the ollama provider.")

        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        endpoint = f"{self.base_url.rstrip('/')}/api/generate"

        try:
            client = httpx.Client(timeout=self.timeout)
            response = client.post(
                endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": self.temperature,
                    },
                },
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                f"Could not connect to Ollama at {self.base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Ollama timeout: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(f"Ollama API error: {exc}") from exc
        except Exception as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        return data.get("response", "") or ""

    # --- parsing ---

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract a JSON object from arbitrary model output.

        Handles:
        - Plain JSON
        - Markdown code fences (```json ... ```)
        - Extra prose before/after JSON
        - Embedded JSON within text
        """
        text = raw.strip()

        # Strip markdown code fences if present.
        if text.startswith("```"):
            lines = text.splitlines()
            # Drop first line (```json / ```) and last (```).
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            text = "\n".join(lines).strip()

        # Try the whole string first.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: locate the first '{' and last '}'.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        # Last resort: try to find a JSON object with regex.
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise LLMParseError("LLM response did not contain valid JSON.")


def build_decision_from_llm(raw: dict) -> AgentDecision | None:
    """Validate raw LLM output into an AgentDecision, or None if invalid."""
    from app.agents.decisions import AgentDecision

    try:
        return AgentDecision(**raw)
    except Exception as exc:
        logger.warning("LLM output failed decision validation: %s", exc)
        return None
