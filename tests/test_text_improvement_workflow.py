from pathlib import Path

from diktux.config import TextImprovementSettings
from diktux.workflows.base import WorkflowPhase
from diktux.workflows.text_improvement import TextImprovementWorkflow


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
        return "roher text"


class FakeLLM:
    def __init__(self):
        self.improve_calls = []

    async def improve(self, text, settings):
        self.improve_calls.append((text, settings))
        return "verbesserter text"


async def test_improvement_workflow(tmp_path: Path):
    rec = FakeRecorder(tmp_path / "a.wav")
    llm = FakeLLM()
    settings = TextImprovementSettings(custom_terms=["DikTux"])
    wf = TextImprovementWorkflow(
        rec, FakeTranscriber(), llm, settings, language="de"
    )
    outputs = []
    wf.on_output = outputs.append
    wf.start()
    await wf.stop()
    assert outputs == ["verbesserter text"]
    assert wf.phase is WorkflowPhase.DONE
    assert llm.improve_calls[0][0] == "roher text"
    assert wf.type == "text_improver"
