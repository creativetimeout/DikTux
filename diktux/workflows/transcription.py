"""Basic dictation workflow: record -> transcribe -> paste."""

from __future__ import annotations

from pathlib import Path

from diktux.workflows.base import BaseWorkflow


class TranscriptionWorkflow(BaseWorkflow):
    def __init__(
        self,
        recorder,
        transcriber,
        custom_terms: list[str] | None = None,
        language: str = "de",
        type_name: str = "transcription",
    ) -> None:
        super().__init__(recorder)
        self.type = type_name
        self._transcriber = transcriber
        self._custom_terms = custom_terms or []
        self._language = language

    async def process(self, audio_path: Path) -> str:
        return await self._transcriber.transcribe(
            audio_path,
            custom_terms=self._custom_terms,
            language=self._language,
        )
