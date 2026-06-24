from pathlib import Path

from diktux.config import EmojiTextSettings
from diktux.workflows.base import WorkflowPhase
from diktux.workflows.emoji_text import EmojiTextWorkflow


class FakeRecorder:
    def __init__(self, path: Path):
        self.last_duration = 2.0
        self._path = path
        self.is_recording = False

    def start(self):
        self.is_recording = True

    def stop(self) -> Path:
        self.is_recording = False
        self._path.write_bytes(b"d")
        return self._path

    def discard(self):
        pass


class FakeTranscriber:
    async def transcribe(self, audio_path, custom_terms=None, language=None):
        return "schoener tag"


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def add_emojis(self, text, settings):
        self.calls.append((text, settings))
        return "schoener tag :)"


async def test_emoji_workflow(tmp_path: Path):
    rec = FakeRecorder(tmp_path / "a.wav")
    llm = FakeLLM()
    settings = EmojiTextSettings()
    wf = EmojiTextWorkflow(rec, FakeTranscriber(), llm, settings)
    outputs = []
    wf.on_output = outputs.append
    wf.start()
    await wf.stop()
    assert outputs == ["schoener tag :)"]
    assert wf.phase is WorkflowPhase.DONE
    assert llm.calls[0][0] == "schoener tag"
    assert wf.type == "emoji_text"
