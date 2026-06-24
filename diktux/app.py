"""Application orchestration: connects hotkeys to workflows and state."""

from __future__ import annotations

from collections.abc import Callable

from diktux.config import Config
from diktux.services.hotkey import HotkeyEvent, HotkeyEventType
from diktux.state import StateManager
from diktux.workflows.transcription import TranscriptionWorkflow


class Application:
    def __init__(
        self,
        config: Config,
        credentials,
        paste_service,
        recorder_factory: Callable[[], object],
        transcriber,
        state: StateManager,
        local_transcriber=None,
        loop_runner: Callable[[object], None] | None = None,
    ) -> None:
        self.config = config
        self.credentials = credentials
        self.paste_service = paste_service
        self._recorder_factory = recorder_factory
        self._transcriber = transcriber
        self._local_transcriber = local_transcriber or transcriber
        self.state = state
        self._loop_runner = loop_runner or (lambda coro: None)
        self._builders: dict[str, Callable[[], object]] = {}

    def register_workflow_builder(
        self, name: str, builder: Callable[[], object]
    ) -> None:
        self._builders[name] = builder

    def build_workflow(self, workflow_name: str):
        if workflow_name in self._builders:
            return self._builders[workflow_name]()

        if workflow_name == "local_transcription":
            return TranscriptionWorkflow(
                self._recorder_factory(),
                self._local_transcriber,
                custom_terms=self.config.text_improvement.custom_terms,
                language=self.config.transcription.language,
                type_name="local_transcription",
            )

        transcriber = (
            self._local_transcriber
            if self.config.app.secure_local_mode_enabled
            else self._transcriber
        )
        return TranscriptionWorkflow(
            self._recorder_factory(),
            transcriber,
            custom_terms=self.config.text_improvement.custom_terms,
            language=self.config.transcription.language,
            type_name="transcription",
        )

    def handle_hotkey_event(self, event: HotkeyEvent) -> None:
        if event.type is HotkeyEventType.DOWN and event.workflow:
            workflow = self.build_workflow(event.workflow)
            self.state.attach_workflow(workflow)
            workflow.start()
        elif event.type is HotkeyEventType.UP:
            workflow = self.state.active_workflow
            if workflow is not None and workflow.is_recording:
                self._loop_runner(workflow.stop())
        elif event.type is HotkeyEventType.CANCEL:
            workflow = self.state.active_workflow
            if workflow is not None:
                workflow.cancel()
            self.state.active_workflow = None
