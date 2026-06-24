import asyncio

from diktux.app import Application
from diktux.config import Config
from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.services.hotkey import HotkeyEvent, HotkeyEventType
from diktux.state import StateManager


class FakePaste:
    def __init__(self):
        self.pasted = []

    def paste(self, text):
        self.pasted.append(text)


class FakeRecorder:
    def __init__(self):
        self.last_duration = 2.0
        self.is_recording = False
        self.started = False

    def start(self):
        self.started = True
        self.is_recording = True

    def stop(self):
        self.is_recording = False
        from pathlib import Path
        import tempfile

        p = Path(tempfile.mkstemp(suffix=".wav")[1])
        p.write_bytes(b"d")
        return p

    def discard(self):
        pass


class FakeTranscriber:
    async def transcribe(self, audio_path, custom_terms=None, language=None):
        return "Hallo aus dem Test"


def _make_app(pending):
    config = Config()
    credentials = CredentialsStore(backend=InMemoryBackend())
    credentials.set_api_key("sk-test")
    paste = FakePaste()
    state = StateManager(paste_service=paste)
    app = Application(
        config=config,
        credentials=credentials,
        paste_service=paste,
        recorder_factory=lambda: FakeRecorder(),
        transcriber=FakeTranscriber(),
        state=state,
        loop_runner=pending.append,
    )
    return app, paste


def test_hotkey_down_starts_workflow():
    pending = []
    app, _ = _make_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    assert app.state.active_workflow is not None
    assert app.state.active_workflow.is_recording is True


def test_hotkey_up_schedules_stop_and_pastes():
    pending = []
    app, paste = _make_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.UP, "transcription"))
    assert len(pending) == 1
    asyncio.run(pending[0])
    assert paste.pasted == ["Hallo aus dem Test"]


def test_hotkey_cancel_aborts():
    pending = []
    app, _ = _make_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.CANCEL, None))
    assert app.state.active_workflow is None
