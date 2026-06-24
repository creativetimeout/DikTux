"""Central state manager: wires workflow lifecycle to paste and tray status."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from diktux.workflows.base import WorkflowPhase


class TrayStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


_PHASE_TO_STATUS = {
    WorkflowPhase.IDLE: TrayStatus.IDLE,
    WorkflowPhase.RECORDING: TrayStatus.RECORDING,
    WorkflowPhase.PROCESSING: TrayStatus.PROCESSING,
    WorkflowPhase.DONE: TrayStatus.SUCCESS,
    WorkflowPhase.ERROR: TrayStatus.ERROR,
}


class StateManager:
    def __init__(
        self,
        paste_service,
        on_tray_status: Callable[[TrayStatus], None] | None = None,
        on_error_message: Callable[[str], None] | None = None,
    ) -> None:
        self._paste = paste_service
        self._on_tray_status = on_tray_status
        self._on_error_message = on_error_message
        self.tray_status = TrayStatus.IDLE
        self.active_workflow = None

    def _set_tray(self, status: TrayStatus) -> None:
        self.tray_status = status
        if self._on_tray_status is not None:
            self._on_tray_status(status)

    def attach_workflow(self, workflow) -> None:
        self.active_workflow = workflow
        workflow.on_output = self.handle_output
        workflow.on_phase_change = self.handle_phase_change
        workflow.on_error = self.handle_error

    def handle_output(self, text: str) -> None:
        self._paste.paste(text)

    def handle_phase_change(self, phase: WorkflowPhase) -> None:
        self._set_tray(_PHASE_TO_STATUS.get(phase, TrayStatus.IDLE))

    def handle_error(self, error: Exception) -> None:
        if self._on_error_message is not None:
            self._on_error_message(str(error))
        self._set_tray(TrayStatus.ERROR)
