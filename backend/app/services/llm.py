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

    Supports Anthropic and OpenAI. Configuration comes from environment
    variables only; credentials are never hardcoded.

    Environment variables:
        LLM_PROVIDER   - "anthropic" or "openai"
        LLM_MODEL      - model id
        LLM_API_KEY    - provider API key
        LLM_MAX_TOKENS - max tokens for the response (optional)
        LLM_TEMPERATURE - sampling temperature (optional, default 0.0)
        LLM_TIMEOUT    - timeout in seconds (optional, default 30)
    """

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: int = 30,
        max_retries: int = 2,
    ) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "")).lower()
        self.model = model or os.getenv("LLM_MODEL", "")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.max_tokens = max_tokens
        self.temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.provider:
            raise ValueError("LLM_PROVIDER is required for RealLLMService.")
        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for RealLLMService.")
        if self.provider not in ("anthropic", "openai"):
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
                return self._openai_generate(prompt, **kwargs)
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
