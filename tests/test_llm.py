import httpx
import pytest

from diktux.config import (
    EmojiDensity,
    EmojiTextSettings,
    TextImprovementSettings,
    TextTone,
)
from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.services.llm import (
    LLMError,
    LLMService,
    RewriteModel,
    build_emoji_prompt,
    build_improvement_prompt,
)


def _store() -> CredentialsStore:
    store = CredentialsStore(backend=InMemoryBackend())
    store.set_api_key("sk-test")
    return store


def test_default_improvement_prompt_contains_lektor():
    prompt = build_improvement_prompt(TextImprovementSettings())
    assert prompt.startswith("Du bist ein Lektor und Schreibassistent.")
    assert "Verwende einen neutralen, klaren Ton" in prompt


def test_improvement_prompt_formal_tone():
    settings = TextImprovementSettings(tone=TextTone.FORMAL)
    prompt = build_improvement_prompt(settings)
    assert "Verwende einen formellen, professionellen Ton" in prompt


def test_improvement_prompt_custom_overrides():
    settings = TextImprovementSettings(
        system_prompt="Mach es kurz.", custom_terms=["DikTux"]
    )
    prompt = build_improvement_prompt(settings)
    assert prompt.startswith("Mach es kurz.")
    assert "DikTux" in prompt


def test_improvement_prompt_includes_context():
    settings = TextImprovementSettings(context="E-Mail an Chef")
    prompt = build_improvement_prompt(settings)
    assert "Kontext: E-Mail an Chef" in prompt


def test_emoji_prompt_density():
    assert "maximal 1-2 pro Absatz" in build_emoji_prompt(EmojiDensity.WENIG)
    assert "etwa alle 1-2 Saetze" in build_emoji_prompt(EmojiDensity.MITTEL)
    assert "mehrere pro Satz" in build_emoji_prompt(EmojiDensity.VIEL)


async def test_complete_success():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  Verbessert  "}}]},
        )

    def client_factory(timeout):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=timeout)

    service = LLMService(credentials=_store(), client_factory=client_factory)
    result = await service.improve("roh", TextImprovementSettings())
    assert result == "Verbessert"
    assert b"gpt-4o-mini" in captured["body"]


async def test_dampf_ablassen_uses_gpt4o():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ruhig"}}]}
        )

    def client_factory(timeout):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=timeout)

    service = LLMService(credentials=_store(), client_factory=client_factory)
    result = await service.dampf_ablassen("wut", "sei ruhig")
    assert result == "ruhig"
    assert b"gpt-4o" in captured["body"]


async def test_complete_no_content_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "  "}}]})

    def client_factory(timeout):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=timeout)

    service = LLMService(credentials=_store(), client_factory=client_factory)
    with pytest.raises(LLMError) as exc:
        await service.improve("roh", TextImprovementSettings())
    assert "Keine Antwort" in str(exc.value)


async def test_complete_not_configured():
    service = LLMService(credentials=CredentialsStore(backend=InMemoryBackend()))
    with pytest.raises(LLMError) as exc:
        await service.improve("roh", TextImprovementSettings())
    assert "API Key fehlt" in str(exc.value)
