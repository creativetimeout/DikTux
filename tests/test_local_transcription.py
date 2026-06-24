from pathlib import Path

import pytest

from diktux.services.local_transcription import (
    RECOMMENDED_MODEL,
    SUPPORTED_MODELS,
    LocalTranscriptionError,
    LocalTranscriptionService,
)


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, segments):
        self._segments = segments
        self.calls = []

    def transcribe(self, audio_path, language=None, initial_prompt=None):
        self.calls.append((audio_path, language, initial_prompt))
        return iter(self._segments), {"language": language}


def test_supported_models_and_recommended():
    assert RECOMMENDED_MODEL == "small"
    assert "large-v3-turbo" in SUPPORTED_MODELS


async def test_transcribe_joins_segments(tmp_path: Path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"d")
    model = FakeModel([FakeSegment(" Hallo"), FakeSegment(" Welt")])

    service = LocalTranscriptionService(
        model_factory=lambda **kw: model, models_dir=tmp_path
    )
    result = await service.transcribe(
        audio, custom_terms=["DikTux"], language="de", model_name="small"
    )
    assert result == "Hallo Welt"
    assert model.calls[0][1] == "de"
    assert model.calls[0][2] == "Eigennamen und Begriffe: DikTux"


async def test_transcribe_empty_raises(tmp_path: Path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"d")
    model = FakeModel([FakeSegment("   ")])
    service = LocalTranscriptionService(
        model_factory=lambda **kw: model, models_dir=tmp_path
    )
    with pytest.raises(LocalTranscriptionError) as exc:
        await service.transcribe(audio, language="de", model_name="small")
    assert "keinen Text" in str(exc.value)


async def test_transcribe_missing_file(tmp_path: Path):
    service = LocalTranscriptionService(
        model_factory=lambda **kw: FakeModel([]), models_dir=tmp_path
    )
    with pytest.raises(LocalTranscriptionError) as exc:
        await service.transcribe(tmp_path / "nope.wav", model_name="small")
    assert "fehlt" in str(exc.value).lower() or "nicht" in str(exc.value).lower()
