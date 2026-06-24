from diktux.state import StateManager, TrayStatus
from diktux.workflows.base import WorkflowPhase


class FakePaste:
    def __init__(self):
        self.pasted = []

    def paste(self, text):
        self.pasted.append(text)


class FakeWorkflow:
    def __init__(self):
        self.on_phase_change = None
        self.on_output = None
        self.on_error = None
        self.type = "transcription"


def test_handle_output_pastes():
    paste = FakePaste()
    state = StateManager(paste_service=paste)
    state.handle_output("hallo")
    assert paste.pasted == ["hallo"]


def test_phase_maps_to_tray_status():
    statuses = []
    state = StateManager(paste_service=FakePaste(), on_tray_status=statuses.append)
    state.handle_phase_change(WorkflowPhase.RECORDING)
    state.handle_phase_change(WorkflowPhase.PROCESSING)
    state.handle_phase_change(WorkflowPhase.DONE)
    assert statuses == [
        TrayStatus.RECORDING,
        TrayStatus.PROCESSING,
        TrayStatus.SUCCESS,
    ]


def test_handle_error_sets_error_status_and_message():
    statuses = []
    messages = []
    state = StateManager(
        paste_service=FakePaste(),
        on_tray_status=statuses.append,
        on_error_message=messages.append,
    )
    state.handle_error(ValueError("kaputt"))
    assert statuses[-1] is TrayStatus.ERROR
    assert messages[-1] == "kaputt"


def test_attach_workflow_wires_callbacks():
    paste = FakePaste()
    state = StateManager(paste_service=paste)
    wf = FakeWorkflow()
    state.attach_workflow(wf)
    wf.on_output("text")
    assert paste.pasted == ["text"]
    assert state.active_workflow is wf
