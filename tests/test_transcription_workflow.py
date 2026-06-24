from pathlib import Path

from diktux.workflows.base import WorkflowPhase
from diktux.workflows.transcription import TranscriptionWorkflow


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
    def __init__(self, text="transkript"):
        self.text = text
        self.calls = []

    async def transcribe(self, audio_path, custom_terms=None, language=None):
        self.calls.append((audio_path, custom_terms, language))
        return self.text


async def test_transcription_workflow_outputs_text(tmp_path: Path):
    rec = FakeRecorder(tmp_path / "a.wav")
    transcriber = FakeTranscriber("Hallo Welt")
    wf = TranscriptionWorkflow(
        rec, transcriber, custom_terms=["DikTux"], language="de"
    )
    outputs = []
    wf.on_output = outputs.append
    wf.start()
    await wf.stop()
    assert outputs == ["Hallo Welt"]
    assert wf.phase is WorkflowPhase.DONE
    assert transcriber.calls[0][1] == ["DikTux"]
    assert transcriber.calls[0][2] == "de"


def test_transcription_workflow_type_name(tmp_path: Path):
    wf = TranscriptionWorkflow(
        FakeRecorder(tmp_path / "a.wav"),
        FakeTranscriber(),
        type_name="local_transcription",
    )
    assert wf.type == "local_transcription"
