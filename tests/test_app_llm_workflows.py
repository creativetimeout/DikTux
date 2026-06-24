from diktux.app import Application
from diktux.config import Config
from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.state import StateManager
from diktux.workflows.calm_down import CalmDownWorkflow
from diktux.workflows.emoji_text import EmojiTextWorkflow
from diktux.workflows.text_improvement import TextImprovementWorkflow


class FakePaste:
    def paste(self, text):
        pass


class FakeRecorder:
    def __init__(self):
        self.last_duration = 2.0
        self.is_recording = False

    def start(self):
        self.is_recording = True

    def stop(self):
        from pathlib import Path
        import tempfile

        p = Path(tempfile.mkstemp(suffix=".wav")[1])
        p.write_bytes(b"d")
        return p

    def discard(self):
        pass


class FakeTranscriber:
    async def transcribe(self, audio_path, custom_terms=None, language=None):
        return "x"


class FakeLLM:
    async def improve(self, text, settings):
        return "i"

    async def dampf_ablassen(self, text, system_prompt):
        return "d"

    async def add_emojis(self, text, settings):
        return "e"


def _app():
    credentials = CredentialsStore(backend=InMemoryBackend())
    credentials.set_api_key("sk-test")
    return Application(
        config=Config(),
        credentials=credentials,
        paste_service=FakePaste(),
        recorder_factory=lambda: FakeRecorder(),
        transcriber=FakeTranscriber(),
        state=StateManager(paste_service=FakePaste()),
        llm=FakeLLM(),
    )


def test_build_text_improver():
    assert isinstance(_app().build_workflow("text_improver"), TextImprovementWorkflow)


def test_build_dampf_ablassen():
    assert isinstance(_app().build_workflow("dampf_ablassen"), CalmDownWorkflow)


def test_build_emoji_text():
    assert isinstance(_app().build_workflow("emoji_text"), EmojiTextWorkflow)
