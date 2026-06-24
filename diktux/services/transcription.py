"""Remote transcription via the OpenAI Whisper API (whisper-1)."""

from __future__ import annotations

from pathlib import Path

import httpx

from diktux.services.credentials import CredentialsStore


class TranscriptionError(Exception):
    @classmethod
    def not_configured(cls) -> "TranscriptionError":
        return cls("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")

    @classmethod
    def network_error(cls, msg: str) -> "TranscriptionError":
        return cls(f"Netzwerkfehler: {msg}")

    @classmethod
    def api_error(cls, msg: str) -> "TranscriptionError":
        return cls(f"OpenAI-Fehler: {msg}")

    @classmethod
    def no_file(cls) -> "TranscriptionError":
        return cls("Keine Audio-Datei gefunden")


class RemoteTranscriptionService:
    MODEL = "whisper-1"
    URL = "https://api.openai.com/v1/audio/transcriptions"
    TIMEOUT = 60.0

    def __init__(
        self, credentials: CredentialsStore, client_factory=None
    ) -> None:
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

    async def transcribe(
        self,
        audio_path: Path,
        custom_terms: list[str] | None = None,
        language: str | None = None,
    ) -> str:
        api_key = self._credentials.get_api_key()
        if not api_key:
            raise TranscriptionError.not_configured()

        if not audio_path.exists():
            raise TranscriptionError.no_file()

        audio_bytes = audio_path.read_bytes()
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": self.MODEL, "response_format": "text"}

        if custom_terms:
            data["prompt"] = "Eigennamen und Begriffe: " + ", ".join(custom_terms)
        if language and language.strip():
            data["language"] = language.strip()

        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with self._client_factory(self.TIMEOUT) as client:
                response = await client.post(
                    self.URL, headers=headers, data=data, files=files
                )
        except httpx.HTTPError as exc:
            raise TranscriptionError.network_error(str(exc)) from exc
        finally:
            try:
                audio_path.unlink()
            except OSError:
                pass

        if response.status_code != 200:
            raise TranscriptionError.api_error(self._error_message(response))

        text = response.text.strip()
        if not text:
            raise TranscriptionError.api_error("Transkription fehlgeschlagen")
        return text
