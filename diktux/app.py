"""Application orchestration: connects hotkeys to workflows and state."""

from __future__ import annotations

from collections.abc import Callable

from diktux.config import Config, HotkeyMode
from diktux.services.hotkey import HotkeyEvent, HotkeyEventType
from diktux.state import StateManager
from diktux.workflows.calm_down import CalmDownWorkflow
from diktux.workflows.emoji_text import EmojiTextWorkflow
from diktux.workflows.text_improvement import TextImprovementWorkflow
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
        llm=None,
        loop_runner: Callable[[object], None] | None = None,
    ) -> None:
        self.config = config
        self.credentials = credentials
        self.paste_service = paste_service
        self._recorder_factory = recorder_factory
        self._transcriber = transcriber
        self._local_transcriber = local_transcriber or transcriber
        self._llm = llm
        self.state = state
        self._loop_runner = loop_runner or (lambda coro: None)
        self._builders: dict[str, Callable[[], object]] = {}

    @property
    def _active_transcriber(self):
        if self.config.app.secure_local_mode_enabled:
            return self._local_transcriber
        return self._transcriber

    def register_workflow_builder(
        self, name: str, builder: Callable[[], object]
    ) -> None:
        self._builders[name] = builder

    def build_workflow(self, workflow_name: str):
        if workflow_name in self._builders:
            return self._builders[workflow_name]()

        if workflow_name == "text_improver":
            return TextImprovementWorkflow(
                self._recorder_factory(),
                self._active_transcriber,
                self._llm,
                self.config.text_improvement,
                language=self.config.transcription.language,
            )

        if workflow_name == "dampf_ablassen":
            return CalmDownWorkflow(
                self._recorder_factory(),
                self._active_transcriber,
                self._llm,
                self.config.dampf_ablassen,
                custom_terms=self.config.text_improvement.custom_terms,
                language=self.config.transcription.language,
            )

        if workflow_name == "emoji_text":
            return EmojiTextWorkflow(
                self._recorder_factory(),
                self._active_transcriber,
                self._llm,
                self.config.emoji_text,
                custom_terms=self.config.text_improvement.custom_terms,
                language=self.config.transcription.language,
            )

        if workflow_name == "local_transcription":
            return TranscriptionWorkflow(
                self._recorder_factory(),
                self._local_transcriber,
                custom_terms=self.config.text_improvement.custom_terms,
                language=self.config.transcription.language,
                type_name="local_transcription",
            )

        return TranscriptionWorkflow(
            self._recorder_factory(),
            self._active_transcriber,
            custom_terms=self.config.text_improvement.custom_terms,
            language=self.config.transcription.language,
            type_name="transcription",
        )

    def handle_hotkey_event(self, event: HotkeyEvent) -> None:
        if event.type is HotkeyEventType.CANCEL:
            workflow = self.state.active_workflow
            if workflow is not None:
                workflow.cancel()
            self.state.active_workflow = None
            return

        if self.config.hotkeys.mode is HotkeyMode.TOGGLE:
            self._handle_toggle(event)
        else:
            self._handle_hold(event)

    def _handle_hold(self, event: HotkeyEvent) -> None:
        if event.type is HotkeyEventType.DOWN and event.workflow:
            workflow = self.build_workflow(event.workflow)
            self.state.attach_workflow(workflow)
            workflow.start()
        elif event.type is HotkeyEventType.UP:
            workflow = self.state.active_workflow
            if workflow is not None and workflow.is_recording:
                self._loop_runner(workflow.stop())

    def _handle_toggle(self, event: HotkeyEvent) -> None:
        if event.type is not HotkeyEventType.DOWN or not event.workflow:
            return

        current = self.state.active_workflow
        if current is not None and current.is_recording:
            self._loop_runner(current.stop())
            return

        workflow = self.build_workflow(event.workflow)
        self.state.attach_workflow(workflow)
        workflow.start()
