from pathlib import Path

from diktux.config import DampfAblassenSettings
from diktux.workflows.base import WorkflowPhase
from diktux.workflows.calm_down import CalmDownWorkflow


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
        return "ich bin so wuetend"


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def dampf_ablassen(self, text, system_prompt):
        self.calls.append((text, system_prompt))
        return "ruhige nachricht"


async def test_calm_down_workflow(tmp_path: Path):
    rec = FakeRecorder(tmp_path / "a.wav")
    llm = FakeLLM()
    settings = DampfAblassenSettings()
    wf = CalmDownWorkflow(rec, FakeTranscriber(), llm, settings)
    outputs = []
    wf.on_output = outputs.append
    wf.start()
    await wf.stop()
    assert outputs == ["ruhige nachricht"]
    assert wf.phase is WorkflowPhase.DONE
    assert llm.calls[0][0] == "ich bin so wuetend"
    assert llm.calls[0][1] == settings.system_prompt
    assert wf.type == "dampf_ablassen"
