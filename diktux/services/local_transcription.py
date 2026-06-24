"""Local transcription via faster-whisper (CTranslate2 backend)."""

from __future__ import annotations

import asyncio
from pathlib import Path

SUPPORTED_MODELS = ("small", "large-v3", "large-v3-turbo")
RECOMMENDED_MODEL = "small"


class LocalTranscriptionError(Exception):
    @classmethod
    def model_missing(cls, name: str) -> "LocalTranscriptionError":
        return cls(f"Audio-Datei fehlt oder lokales Modell '{name}' nicht verfügbar.")

    @classmethod
    def no_text(cls) -> "LocalTranscriptionError":
        return cls("Das lokale Modell hat keinen Text erkannt.")


def models_dir() -> Path:
    return Path.home() / ".local" / "share" / "diktux" / "models"


class LocalTranscriptionService:
    def __init__(
        self,
        model_factory=None,
        models_dir: Path | None = None,
        device: str = "auto",
        compute_type: str = "int8",
    ) -> None:
        self._model_factory = model_factory or self._default_model_factory
        self._models_dir = Path(models_dir) if models_dir else globals()["models_dir"]()
        self._device = device
        self._compute_type = compute_type
        self._cache: dict[str, object] = {}

    @staticmethod
    def _default_model_factory(model_name, device, compute_type, download_root):
        from faster_whisper import WhisperModel

        return WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root=download_root,
        )

    def _get_model(self, model_name: str):
        if model_name not in self._cache:
            self._cache[model_name] = self._model_factory(
                model_name=model_name,
                device=self._device,
                compute_type=self._compute_type,
                download_root=str(self._models_dir),
            )
        return self._cache[model_name]

    def is_model_available(self, model_name: str) -> bool:
        return (self._models_dir / f"models--Systran--faster-whisper-{model_name}").exists()

    def _transcribe_sync(
        self,
        audio_path: Path,
        custom_terms: list[str] | None,
        language: str,
        model_name: str,
    ) -> str:
        if not audio_path.exists():
            raise LocalTranscriptionError.model_missing(model_name)

        self._models_dir.mkdir(parents=True, exist_ok=True)
        model = self._get_model(model_name)

        initial_prompt = None
        if custom_terms:
            initial_prompt = "Eigennamen und Begriffe: " + ", ".join(custom_terms)

        resolved_language = language.strip() or None
        segments, _info = model.transcribe(
            str(audio_path),
            language=resolved_language,
            initial_prompt=initial_prompt,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if not text:
            raise LocalTranscriptionError.no_text()
        return text

    async def transcribe(
        self,
        audio_path: Path,
        custom_terms: list[str] | None = None,
        language: str = "de",
        model_name: str = RECOMMENDED_MODEL,
    ) -> str:
        try:
            return await asyncio.to_thread(
                self._transcribe_sync,
                audio_path,
                custom_terms,
                language,
                model_name,
            )
        finally:
            try:
                audio_path.unlink()
            except OSError:
                pass
