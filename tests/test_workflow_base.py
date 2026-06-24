from pathlib import Path

import pytest

from diktux.services.audio_recorder import AudioRecorder
from diktux.workflows.base import (
    ArtifactError,
    BaseWorkflow,
    RecordingTooShortError,
    WorkflowPhase,
)


class FakeRecorder:
    def __init__(self, duration: float, path: Path):
        self.last_duration = duration
        self._path = path
        self.is_recording = False
        self.started = False
        self.discarded = False

    def start(self):
        self.started = True
        self.is_recording = True

    def stop(self) -> Path:
        self.is_recording = False
        self._path.write_bytes(b"data")
        return self._path

    def discard(self):
        self.discarded = True


class EchoWorkflow(BaseWorkflow):
    def __init__(self, recorder, text="ergebnis"):
        super().__init__(recorder)
        self.type = "echo"
        self._text = text

    async def process(self, audio_path: Path) -> str:
        return self._text


async def test_start_sets_recording_phase(tmp_path: Path):
    wf = EchoWorkflow(FakeRecorder(2.0, tmp_path / "a.wav"))
    phases = []
    wf.on_phase_change = phases.append
    wf.start()
    assert wf.phase is WorkflowPhase.RECORDING
    assert wf.is_recording is True
    assert phases[-1] is WorkflowPhase.RECORDING


async def test_stop_runs_process_and_emits_output(tmp_path: Path):
    wf = EchoWorkflow(FakeRecorder(2.0, tmp_path / "a.wav"), text="fertig")
    outputs = []
    wf.on_output = outputs.append
    wf.start()
    await wf.stop()
    assert outputs == ["fertig"]
    assert wf.phase is WorkflowPhase.DONE


async def test_stop_rejects_short_recording(tmp_path: Path):
    wf = EchoWorkflow(FakeRecorder(0.1, tmp_path / "a.wav"))
    errors = []
    wf.on_error = errors.append
    wf.start()
    await wf.stop()
    assert wf.phase is WorkflowPhase.ERROR
    assert isinstance(errors[-1], RecordingTooShortError)


async def test_cancel_discards(tmp_path: Path):
    rec = FakeRecorder(2.0, tmp_path / "a.wav")
    wf = EchoWorkflow(rec)
    wf.start()
    wf.cancel()
    assert rec.discarded is True
    assert wf.phase is WorkflowPhase.IDLE


async def test_artifact_output_is_error(tmp_path: Path):
    class ArtifactWorkflow(EchoWorkflow):
        async def process(self, audio_path):
            return "x" * 60  # long text, but recording was short

    wf = ArtifactWorkflow(FakeRecorder(0.7, tmp_path / "a.wav"))
    errors = []
    wf.on_error = errors.append
    wf.start()
    await wf.stop()
    assert wf.phase is WorkflowPhase.ERROR
    assert isinstance(errors[-1], ArtifactError)
