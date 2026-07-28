from pydantic import BaseModel

from ai_eval.utils import llm as llm_module
from ai_eval.utils.llm import LLMProvider


class TinyResult(BaseModel):
    answer: str


def test_openai_failure_falls_back_to_anthropic(monkeypatch):
    monkeypatch.setattr(llm_module, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(llm_module, "ANTHROPIC_API_KEY", "anthropic-key")

    def fail_openai(*args, **kwargs):
        raise RuntimeError("openai failed")

    def succeed_anthropic(*args, **kwargs):
        return TinyResult(answer="anthropic"), {
            "latency_ms": 1,
            "cost_usd": 0,
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
        }

    monkeypatch.setattr(LLMProvider, "_call_openai", fail_openai)
    monkeypatch.setattr(LLMProvider, "_call_anthropic", succeed_anthropic)

    provider = LLMProvider(provider="openai")
    result, metadata = provider.call_structured("system", "user", TinyResult)

    assert result.answer == "anthropic"
    assert metadata["provider"] == "anthropic"


def test_both_provider_failures_raise_key_error(monkeypatch):
    monkeypatch.setattr(llm_module, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(llm_module, "ANTHROPIC_API_KEY", "anthropic-key")

    def fail_provider(*args, **kwargs):
        raise RuntimeError("provider failed")

    monkeypatch.setattr(LLMProvider, "_call_openai", fail_provider)
    monkeypatch.setattr(LLMProvider, "_call_anthropic", fail_provider)

    provider = LLMProvider(provider="openai")

    try:
        provider.call_structured("system", "user", TinyResult)
    except RuntimeError as exc:
        assert "API keys not working" in str(exc)
        assert "Please change or add new API keys" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when both providers fail")
