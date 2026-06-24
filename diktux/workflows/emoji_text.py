"""Dictation + emoji enrichment workflow."""

from __future__ import annotations

from pathlib import Path

from diktux.config import EmojiTextSettings
from diktux.workflows.base import BaseWorkflow


class EmojiTextWorkflow(BaseWorkflow):
    def __init__(
        self,
        recorder,
        transcriber,
        llm,
        settings: EmojiTextSettings,
        custom_terms: list[str] | None = None,
        language: str = "de",
    ) -> None:
        super().__init__(recorder)
        self.type = "emoji_text"
        self._transcriber = transcriber
        self._llm = llm
        self._settings = settings
        self._custom_terms = custom_terms or []
        self._language = language

    async def process(self, audio_path: Path) -> str:
        text = await self._transcriber.transcribe(
            audio_path,
            custom_terms=self._custom_terms,
            language=self._language,
        )
        return await self._llm.add_emojis(text, self._settings)
