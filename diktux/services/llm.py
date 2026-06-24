"""LLM post-processing via OpenAI Chat Completions with ported system prompts."""

from __future__ import annotations

from enum import Enum

import httpx

from diktux.config import (
    EmojiDensity,
    EmojiTextSettings,
    TextImprovementSettings,
    TextTone,
)
from diktux.services.credentials import CredentialsStore


class LLMError(Exception):
    @classmethod
    def not_configured(cls) -> "LLMError":
        return cls("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")

    @classmethod
    def network_error(cls, msg: str) -> "LLMError":
        return cls(f"Verbindungsproblem: {msg}")

    @classmethod
    def api_error(cls, msg: str) -> "LLMError":
        return cls(f"Fehler von OpenAI: {msg}")

    @classmethod
    def no_content(cls) -> "LLMError":
        return cls("Keine Antwort erhalten. Bitte nochmal versuchen.")


class RewriteModel(str, Enum):
    FAST_EDIT = "gpt-4o-mini"
    RAGE_MODE = "gpt-4o"


def build_emoji_prompt(density: EmojiDensity) -> str:
    if density is EmojiDensity.WENIG:
        density_instruction = "Setze nur vereinzelt Emojis ein, maximal 1-2 pro Absatz."
    elif density is EmojiDensity.VIEL:
        density_instruction = "Setze grosszuegig Emojis ein, gerne mehrere pro Satz."
    else:
        density_instruction = (
            "Setze regelmaessig passende Emojis ein, etwa alle 1-2 Saetze."
        )

    return (
        "Du erhaeltst ein gesprochenes Transkript. Gib den Text moeglichst "
        "originalgetreu zurueck, aber fuege passende Emojis ein. "
        f"{density_instruction} Korrigiere offensichtliche Sprach- und "
        "Grammatikfehler. Behalte den Stil und die Bedeutung bei. Gib NUR den "
        "Text mit Emojis zurueck, keine Erklaerungen."
    )


def build_improvement_prompt(settings: TextImprovementSettings) -> str:
    if settings.system_prompt:
        prompt = settings.system_prompt
        if settings.custom_terms:
            prompt += (
                "\n\nWichtig: Diese Eigennamen und Fachbegriffe muessen exakt so "
                "geschrieben werden: " + ", ".join(settings.custom_terms)
            )
        return prompt

    prompt = (
        "Du bist ein Lektor und Schreibassistent. Verbessere den folgenden Text:\n"
        "- Korrigiere Rechtschreibung und Grammatik\n"
        "- Verbessere die Formulierung und den Lesefluss\n"
        "- Behalte die urspruengliche Bedeutung bei\n"
        "- Gib NUR den verbesserten Text zurueck, keine Erklaerungen"
    )

    if settings.tone is TextTone.FORMAL:
        prompt += "\n- Verwende einen formellen, professionellen Ton"
    elif settings.tone is TextTone.NEUTRAL:
        prompt += "\n- Verwende einen neutralen, klaren Ton"
    elif settings.tone is TextTone.CASUAL:
        prompt += "\n- Verwende einen lockeren, natuerlichen Ton"

    if settings.custom_terms:
        prompt += (
            "\n\nWichtig: Diese Eigennamen und Fachbegriffe muessen exakt so "
            "geschrieben werden: " + ", ".join(settings.custom_terms)
        )

    if settings.context:
        prompt += "\n\nKontext: " + settings.context

    return prompt


class LLMService:
    URL = "https://api.openai.com/v1/chat/completions"
    TIMEOUT = 45.0

    def __init__(self, credentials: CredentialsStore, client_factory=None) -> None:
        self._credentials = credentials
        self._client_factory = client_factory or self._default_client_factory

    @staticmethod
    def _default_client_factory(timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout)

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
            message = payload.get("error", {}).get("message")
            if message:
                return message
        except (ValueError, AttributeError):
            pass
        return f"Status {response.status_code}"

    async def complete(
        self,
        text: str,
        system_prompt: str,
        model: RewriteModel,
        temperature: float,
    ) -> str:
        api_key = self._credentials.get_api_key()
        if not api_key:
            raise LLMError.not_configured()

        payload = {
            "model": model.value,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with self._client_factory(self.TIMEOUT) as client:
                response = await client.post(
                    self.URL, headers=headers, json=payload
                )
        except httpx.HTTPError as exc:
            raise LLMError.network_error(str(exc)) from exc

        if response.status_code != 200:
            raise LLMError.api_error(self._error_message(response))

        try:
            choices = response.json().get("choices") or []
            content = choices[0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMError.no_content()

        if content is None or not content.strip():
            raise LLMError.no_content()
        return content.strip()

    async def improve(
        self,
        text: str,
        settings: TextImprovementSettings,
        model: RewriteModel = RewriteModel.FAST_EDIT,
    ) -> str:
        return await self.complete(
            text, build_improvement_prompt(settings), model, 0.3
        )

    async def dampf_ablassen(
        self,
        text: str,
        system_prompt: str,
        model: RewriteModel = RewriteModel.RAGE_MODE,
    ) -> str:
        return await self.complete(text, system_prompt, model, 0.4)

    async def add_emojis(
        self,
        text: str,
        settings: EmojiTextSettings,
        model: RewriteModel = RewriteModel.FAST_EDIT,
    ) -> str:
        return await self.complete(
            text, build_emoji_prompt(settings.emoji_density), model, 0.3
        )
