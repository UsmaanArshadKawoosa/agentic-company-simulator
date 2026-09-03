"""Focused tests for the Gemini and Ollama LLM providers.

All external calls (Google Gemini SDK, Ollama HTTP API) are mocked so the
suite runs without an API key or a locally running Ollama instance.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import httpx
import pytest
from types import SimpleNamespace

from app.services.llm import (
    LLMParseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    RealLLMService,
)
from app.services.llm import LLMService
from app.simulation.engine import SimulationEngine, _build_llm_from_config


@pytest.fixture(autouse=True)
def _clear_llm_env(monkeypatch):
    """Isolate tests from a real environment / .env so construction is deterministic."""
    for var in ("LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "OLLAMA_BASE_URL",
                "LLM_MAX_TOKENS", "LLM_TEMPERATURE", "LLM_TIMEOUT", "LLM_MAX_RETRIES"):
        monkeypatch.delenv(var, raising=False)


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

VALID_DECISION = '{"action": "NO_ACTION", "reasoning": "ok", "confidence": 0.5}'


def _gemini_llm(api_key="test-gemini-key", **kwargs):
    return RealLLMService(provider="gemini", api_key=api_key, **kwargs)


def _ollama_llm(model="gemma2", **kwargs):
    return RealLLMService(provider="ollama", model=model, **kwargs)


def _install_fake_genai(monkeypatch, response_text=VALID_DECISION, raise_exc=None):
    """Inject a fake ``google.genai`` module tree into sys.modules.

    The real ``google-genai`` package is imported lazily inside
    ``_gemini_generate``; populating ``sys.modules`` lets us exercise the real
    provider code path without installing the SDK.

    Returns a handle with ``calls`` (list of generate_content kwargs) so tests
    can assert on the model / prompt passed.
    """
    calls = []

    class _Response:
        def __init__(self, text):
            self.text = text

    class _Models:
        def generate_content(self, model=None, contents=None, config=None):
            calls.append({"model": model, "contents": contents, "config": config})
            if raise_exc is not None:
                raise raise_exc
            return _Response(response_text)

    class _Client:
        instances = []

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            type(self).instances.append(self)

        @property
        def models(self):
            return _Models()

    google = types.ModuleType("google")
    genai = types.ModuleType("google.genai")
    genai_types = types.ModuleType("google.genai.types")
    genai.Client = _Client
    genai_types.GenerateContentConfig = lambda **kw: kw
    genai.types = genai_types
    google.genai = genai

    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", genai_types)
    monkeypatch.setattr(genai, "Client", _Client, raising=False)
    return SimpleNamespace(calls=calls, client_class=_Client)


class _FakeOllamaResponse:
    """Mimics the JSON body Ollama's /api/generate returns.

    Ollama responds with an object whose ``response`` field holds the model's
    generated text (which may itself be JSON for our structured use case).
    """

    def __init__(self, response_text, status_code=200):
        self._response_text = response_text
        self.status_code = status_code

    def json(self):
        return {"response": self._response_text, "done": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "err", request=httpx.Request("POST", "http://x"), response=self
            )


class _FakeOllamaClient:
    def __init__(self, response_text=VALID_DECISION, connect_exc=None,
                 timeout_exc=None, status_code=200):
        self.response_text = response_text
        self.connect_exc = connect_exc
        self.timeout_exc = timeout_exc
        self.status_code = status_code
        self.post_calls = []

    def post(self, url, json=None, **kwargs):
        self.post_calls.append((url, json))
        if self.connect_exc is not None:
            raise self.connect_exc
        if self.timeout_exc is not None:
            raise self.timeout_exc
        return _FakeOllamaResponse(self.response_text, status_code=self.status_code)


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------


class TestGeminiProviderSelection:
    def test_accepts_gemini(self):
        llm = RealLLMService(provider="gemini", api_key="test-key")
        assert llm.provider == "gemini"

    def test_gemini_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            RealLLMService(provider="gemini", api_key="")

    def test_gemini_uses_default_model(self, monkeypatch):
        handle = _install_fake_genai(monkeypatch, response_text=VALID_DECISION)
        llm = RealLLMService(provider="gemini", api_key="k")  # no model
        llm._gemini_generate("hi")
        assert handle.calls[-1]["model"] == "gemini-2.5-flash"


class TestOllamaProviderSelection:
    def test_accepts_ollama(self):
        llm = RealLLMService(provider="ollama", model="gemma2")
        assert llm.provider == "ollama"

    def test_ollama_does_not_require_api_key(self):
        llm = RealLLMService(provider="ollama", api_key="")
        assert llm.provider == "ollama"

    def test_ollama_default_base_url(self):
        llm = RealLLMService(provider="ollama", model="gemma2")
        assert llm.base_url == "http://localhost:11434"

    def test_ollama_custom_base_url(self):
        llm = RealLLMService(provider="ollama", model="gemma2",
                             base_url="http://localhost:11435")
        assert llm.base_url == "http://localhost:11435"

    def test_ollama_requires_model(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        llm = RealLLMService(provider="ollama", api_key="")
        with pytest.raises(LLMProviderError, match="LLM_MODEL"):
            llm._ollama_generate("prompt")


# ---------------------------------------------------------------------------
# Successful response parsing (real provider code paths, mocked transport)
# ---------------------------------------------------------------------------


class TestGeminiResponseParsing:
    def test_successful_response_parsing(self, monkeypatch):
        _install_fake_genai(monkeypatch, response_text=VALID_DECISION)
        llm = _gemini_llm()
        result = llm.structured_generate("decide something")
        assert result["action"] == "NO_ACTION"
        assert result["confidence"] == 0.5


class TestOllamaResponseParsing:
    def test_successful_response_parsing(self, monkeypatch):
        fake = _FakeOllamaClient(response_text=VALID_DECISION)
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
        llm = _ollama_llm()
        result = llm.structured_generate("decide something")
        assert result["action"] == "NO_ACTION"
        assert result["confidence"] == 0.5
        assert fake.post_calls[0][0].endswith("/api/generate")

    def test_ollama_extracts_response_field(self, monkeypatch):
        fake = _FakeOllamaClient(
            response_text='{"action": "HIRE", "reasoning": "need people", "confidence": 0.9}'
        )
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
        llm = _ollama_llm()
        assert llm._ollama_generate("prompt") == '{"action": "HIRE", "reasoning": "need people", "confidence": 0.9}'


# ---------------------------------------------------------------------------
# Malformed JSON handling
# ---------------------------------------------------------------------------


class TestMalformedJson:
    def test_gemini_malformed_json(self, monkeypatch):
        _install_fake_genai(monkeypatch, response_text="this is not json")
        llm = _gemini_llm()
        with pytest.raises(LLMParseError):
            llm.structured_generate("decide")

    def test_ollama_malformed_json(self, monkeypatch):
        fake = _FakeOllamaClient(response_text="<<<not json>>>")
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
        llm = _ollama_llm()
        with pytest.raises(LLMParseError):
            llm.structured_generate("decide")

    def test_ollama_malformed_via_mock(self, monkeypatch):
        llm = _ollama_llm()
        monkeypatch.setattr(llm, "_ollama_generate", lambda prompt, **kw: "nope not json")
        with pytest.raises(LLMParseError):
            llm.structured_generate("decide")


# ---------------------------------------------------------------------------
# Timeout behavior
# ---------------------------------------------------------------------------


class TestTimeoutBehavior:
    def test_gemini_timeout_not_retried(self, monkeypatch):
        calls = {"n": 0}

        def fake_generate(prompt, **kw):
            calls["n"] += 1
            raise LLMTimeoutError("timed out")

        llm = _gemini_llm(max_retries=3)
        monkeypatch.setattr(llm, "_gemini_generate", fake_generate)
        with pytest.raises(LLMTimeoutError):
            llm.generate("hi")
        assert calls["n"] == 1

    def test_ollama_timeout_not_retried(self, monkeypatch):
        calls = {"n": 0}

        def fake_generate(prompt, **kw):
            calls["n"] += 1
            raise LLMTimeoutError("timed out")

        llm = _ollama_llm(max_retries=3)
        monkeypatch.setattr(llm, "_ollama_generate", fake_generate)
        with pytest.raises(LLMTimeoutError):
            llm.generate("hi")
        assert calls["n"] == 1


# ---------------------------------------------------------------------------
# Retry behavior
# ---------------------------------------------------------------------------


class TestRetryBehavior:
    def test_gemini_retries_transient_then_succeeds(self, monkeypatch):
        llm = _gemini_llm(max_retries=2)
        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = [
            LLMProviderError("transient"),
            LLMProviderError("transient"),
            SimpleNamespace(text=VALID_DECISION),
        ]
        google = types.ModuleType("google")
        genai = types.SimpleNamespace(
            Client=MagicMock(return_value=fake_client),
            types=types.SimpleNamespace(GenerateContentConfig=lambda **kw: kw),
        )
        google.genai = genai
        monkeypatch.setitem(sys.modules, "google", google)
        monkeypatch.setitem(sys.modules, "google.genai", genai)
        monkeypatch.setitem(sys.modules, "google.genai.types", genai.types)

        result = llm.structured_generate("decide")
        assert result["action"] == "NO_ACTION"
        assert fake_client.models.generate_content.call_count == 3

    def test_ollama_retries_transient_then_succeeds(self, monkeypatch):
        llm = _ollama_llm(max_retries=2)
        seq = [
            _FakeOllamaClient(connect_exc=LLMProviderError("transient")),
            _FakeOllamaClient(connect_exc=LLMProviderError("transient")),
            _FakeOllamaClient(response_text=VALID_DECISION),
        ]
        idx = {"i": 0}

        class _Switcher:
            def post(self, url, json=None, **kwargs):
                c = seq[idx["i"]]
                idx["i"] += 1
                return c.post(url, json=json, **kwargs)

        monkeypatch.setattr(httpx, "Client", lambda **kw: _Switcher())
        result = llm.structured_generate("decide")
        assert result["action"] == "NO_ACTION"
        assert idx["i"] == 3

    def test_gemini_retries_exhausted_raises_provider_error(self):
        llm = _gemini_llm(max_retries=1)

        def fake_generate(prompt, **kw):
            raise LLMProviderError("transient")

        llm._gemini_generate = fake_generate  # bypass real dispatch
        with pytest.raises(LLMProviderError, match="after 2 attempts"):
            llm.generate("hi")

    def test_rate_limit_not_retried(self, monkeypatch):
        llm = _gemini_llm(max_retries=3)

        def fake_generate(prompt, **kw):
            raise LLMRateLimitError("slow down")

        monkeypatch.setattr(llm, "_gemini_generate", fake_generate)
        with pytest.raises(LLMRateLimitError):
            llm.generate("hi")


# ---------------------------------------------------------------------------
# Ollama connection failure
# ---------------------------------------------------------------------------


class TestOllamaConnectionFailure:
    def test_connection_error_wrapped(self, monkeypatch):
        fake = _FakeOllamaClient(connect_exc=httpx.ConnectError("connection refused"))
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
        llm = _ollama_llm()
        with pytest.raises(LLMProviderError, match="Could not connect to Ollama"):
            llm._ollama_generate("prompt")

    def test_connection_failure_does_not_crash_engine(self, db, monkeypatch):
        """When Ollama is unreachable the engine still advances the sim."""
        from app.enums import AgentRole, CompanyStatus
        from app.models.agent import Agent
        from app.models.company import Company

        company = Company(name="ConnCo", mission="m", status=CompanyStatus.RUNNING, seed=7)
        db.add(company)
        db.flush()
        for role, auth in [(AgentRole.CEO, 10), (AgentRole.CTO, 8),
                           (AgentRole.CMO, 7), (AgentRole.ENGINEER, 5)]:
            db.add(Agent(company_id=company.id, name=role.value,
                         role=role, authority=auth, capacity=5.0))
        db.commit()

        fake = _FakeOllamaClient(connect_exc=httpx.ConnectError("refused"))
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)

        llm = RealLLMService(
            provider="ollama", model="gemma2", max_retries=0, api_key=""
        )
        engine = SimulationEngine(llm=llm)
        state = engine.tick(db, company.id)
        # Simulation continued despite Ollama being down.
        assert state.current_day == 2


# ---------------------------------------------------------------------------
# API key isolation
# ---------------------------------------------------------------------------


class TestApiKeyIsolation:
    def test_gemini_error_does_not_leak_api_key(self, monkeypatch):
        key = "sk-super-secret-gemini-key-12345"
        # Drive the *real* _gemini_generate path: a fake SDK that raises an
        # error message containing the key. The provider must scrub it.
        _install_fake_genai(
            monkeypatch,
            raise_exc=RuntimeError(f"auth failed with key={key}"),
        )
        llm = RealLLMService(provider="gemini", api_key=key, max_retries=0)
        with pytest.raises(LLMProviderError) as excinfo:
            llm.generate("hi")
        assert key not in str(excinfo.value)


# ---------------------------------------------------------------------------
# Provider isolation
# ---------------------------------------------------------------------------


class TestProviderIsolation:
    def test_instances_are_independent(self):
        gemini = RealLLMService(provider="gemini", api_key="g")
        ollama = RealLLMService(provider="ollama", model="m")
        assert gemini.provider == "gemini"
        assert ollama.provider == "ollama"
        assert ollama.base_url == "http://localhost:11434"
        assert gemini.api_key == "g"
        # ollama does not carry an API key.
        assert ollama.api_key == ""
        # No shared mutable state: mutating one instance must not touch the other.
        gemini.api_key = "changed"
        assert ollama.api_key == ""

    def test_gemini_failure_does_not_affect_ollama(self, monkeypatch):
        gemini = RealLLMService(provider="gemini", api_key="g")
        ollama = RealLLMService(provider="ollama", model="m")

        def gemini_fail(prompt, **kw):
            raise LLMProviderError("gemini down")

        def ollama_ok(prompt, **kw):
            return VALID_DECISION

        monkeypatch.setattr(gemini, "_gemini_generate", gemini_fail)
        monkeypatch.setattr(ollama, "_ollama_generate", ollama_ok)

        with pytest.raises(LLMProviderError):
            gemini.generate("hi")
        result = ollama.structured_generate("hi")
        assert result["action"] == "NO_ACTION"


# ---------------------------------------------------------------------------
# Switching providers without changing simulation code
# ---------------------------------------------------------------------------


class TestProviderSwitching:
    @pytest.mark.parametrize(
        "provider, expected_type_name",
        [
            ("noop", "NoOpLLMService"),
            ("mock", "MockLLMService"),
            ("gemini", "RealLLMService"),
            ("ollama", "RealLLMService"),
        ],
    )
    def test_factory_returns_expected_type(self, monkeypatch, provider, expected_type_name):
        fake = SimpleNamespace(
            LLM_PROVIDER=provider,
            LLM_MODEL="gemini-2.5-flash" if provider == "gemini" else (
                "gemma2" if provider == "ollama" else ""),
            LLM_API_KEY="test-key" if provider in ("gemini",) else "",
            OLLAMA_BASE_URL="http://localhost:11434",
            LLM_MAX_TOKENS=1024,
            LLM_TEMPERATURE=0.0,
            LLM_TIMEOUT=30,
            LLM_MAX_RETRIES=0,
        )
        monkeypatch.setattr("app.config.settings", fake)
        service = _build_llm_from_config()
        assert type(service).__name__ == expected_type_name

    def test_factory_still_supports_anthropic_and_openai(self, monkeypatch):
        for provider in ("anthropic", "openai"):
            fake = SimpleNamespace(
                LLM_PROVIDER=provider,
                LLM_MODEL="",
                LLM_API_KEY="test-key",
                OLLAMA_BASE_URL="http://localhost:11434",
                LLM_MAX_TOKENS=1024,
                LLM_TEMPERATURE=0.0,
                LLM_TIMEOUT=30,
                LLM_MAX_RETRIES=0,
            )
            monkeypatch.setattr("app.config.settings", fake)
            service = _build_llm_from_config()
            assert isinstance(service, RealLLMService)
            assert service.provider == provider

    def test_engine_accepts_gemini_and_ollama(self, monkeypatch):
        """Engine treats any LLMService uniformly; no provider branching in engine."""
        gemini = RealLLMService(provider="gemini", api_key="g", max_retries=0)
        ollama = RealLLMService(provider="ollama", model="m", max_retries=0)

        def gemini_ok(prompt, **kw):
            return VALID_DECISION

        def ollama_ok(prompt, **kw):
            return VALID_DECISION

        monkeypatch.setattr(gemini, "_gemini_generate", gemini_ok)
        monkeypatch.setattr(ollama, "_ollama_generate", ollama_ok)

        assert isinstance(gemini, LLMService)
        assert isinstance(ollama, LLMService)
        # Each parses identically through the central retry/parse path.
        assert gemini.structured_generate("hi")["action"] == "NO_ACTION"
        assert ollama.structured_generate("hi")["action"] == "NO_ACTION"
