import asyncio

from diktux.app import Application
from diktux.config import Config, HotkeyMode
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

    def start(self):
        self.is_recording = True

    def stop(self):
        from pathlib import Path
        import tempfile

        self.is_recording = False
        p = Path(tempfile.mkstemp(suffix=".wav")[1])
        p.write_bytes(b"d")
        return p

    def discard(self):
        self.is_recording = False


class FakeTranscriber:
    async def transcribe(self, audio_path, custom_terms=None, language=None):
        return "Toggle-Text"


def _toggle_app(pending):
    config = Config()
    config.app.hotkey_mode = HotkeyMode.TOGGLE
    config.hotkeys.mode = HotkeyMode.TOGGLE
    credentials = CredentialsStore(backend=InMemoryBackend())
    credentials.set_api_key("sk-test")
    paste = FakePaste()
    return (
        Application(
            config=config,
            credentials=credentials,
            paste_service=paste,
            recorder_factory=lambda: FakeRecorder(),
            transcriber=FakeTranscriber(),
            state=StateManager(paste_service=paste),
            loop_runner=pending.append,
        ),
        paste,
    )


def test_toggle_first_down_starts():
    pending = []
    app, _ = _toggle_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    assert app.state.active_workflow is not None
    assert app.state.active_workflow.is_recording is True


def test_toggle_up_is_ignored():
    pending = []
    app, _ = _toggle_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.UP, "transcription"))
    assert pending == []
    assert app.state.active_workflow.is_recording is True


def test_toggle_second_down_stops_and_pastes():
    pending = []
    app, paste = _toggle_app(pending)
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    app.handle_hotkey_event(HotkeyEvent(HotkeyEventType.DOWN, "transcription"))
    assert len(pending) == 1
    asyncio.run(pending[0])
    assert paste.pasted == ["Toggle-Text"]
