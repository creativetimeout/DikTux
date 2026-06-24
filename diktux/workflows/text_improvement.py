"""Dictation + text improvement workflow."""

from __future__ import annotations

from pathlib import Path

from diktux.config import TextImprovementSettings
from diktux.workflows.base import BaseWorkflow


class TextImprovementWorkflow(BaseWorkflow):
    def __init__(
        self,
        recorder,
        transcriber,
        llm,
        settings: TextImprovementSettings,
        language: str = "de",
    ) -> None:
        super().__init__(recorder)
        self.type = "text_improver"
        self._transcriber = transcriber
        self._llm = llm
        self._settings = settings
        self._language = language

    async def process(self, audio_path: Path) -> str:
        text = await self._transcriber.transcribe(
            audio_path,
            custom_terms=self._settings.custom_terms,
            language=self._language,
        )
        return await self._llm.improve(text, self._settings)
