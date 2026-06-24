from pathlib import Path

import httpx
import pytest

from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.services.transcription import (
    RemoteTranscriptionService,
    TranscriptionError,
)


def _store_with_key() -> CredentialsStore:
    store = CredentialsStore(backend=InMemoryBackend())
    store.set_api_key("sk-test")
    return store


def _audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "a.wav"
    path.write_bytes(b"RIFFfake")
    return path


async def test_transcribe_success(tmp_path: Path):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers["Authorization"]
        captured["body"] = request.content
        return httpx.Response(200, text="Hallo Welt")

    transport = httpx.MockTransport(handler)

    def client_factory(timeout):
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    service = RemoteTranscriptionService(
        credentials=_store_with_key(), client_factory=client_factory
    )
    result = await service.transcribe(
        _audio_file(tmp_path), custom_terms=["DikTux"], language="de"
    )
    assert result == "Hallo Welt"
    assert captured["auth"] == "Bearer sk-test"
    assert b"whisper-1" in captured["body"]
    assert b"Eigennamen und Begriffe: DikTux" in captured["body"]


async def test_transcribe_not_configured(tmp_path: Path):
    service = RemoteTranscriptionService(
        credentials=CredentialsStore(backend=InMemoryBackend())
    )
    with pytest.raises(TranscriptionError) as exc:
        await service.transcribe(_audio_file(tmp_path))
    assert "API Key fehlt" in str(exc.value)


async def test_transcribe_api_error(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": "Invalid key"}}
        )

    transport = httpx.MockTransport(handler)

    def client_factory(timeout):
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    service = RemoteTranscriptionService(
        credentials=_store_with_key(), client_factory=client_factory
    )
    with pytest.raises(TranscriptionError) as exc:
        await service.transcribe(_audio_file(tmp_path))
    assert "Invalid key" in str(exc.value)


async def test_transcribe_missing_file(tmp_path: Path):
    service = RemoteTranscriptionService(credentials=_store_with_key())
    with pytest.raises(TranscriptionError) as exc:
        await service.transcribe(tmp_path / "nope.wav")
    assert "Keine Audio-Datei" in str(exc.value)
